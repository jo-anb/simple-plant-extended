"""
Custom integration to integrate simple_plant with Home Assistant.

For more details about this integration, please refer to
https://github.com/jo-anb/simple-plant-extended
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.components.logbook import async_log_entry
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import EVENT_STATE_CHANGED
from homeassistant.core import Event, async_get_hass
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.translation import async_get_translations
from homeassistant.helpers.config_validation import config_entry_only_config_schema
from homeassistant.helpers.device_registry import (
    EVENT_DEVICE_REGISTRY_UPDATED,
    EventDeviceRegistryUpdatedData,
    async_entries_for_config_entry,
    async_get,
)
from homeassistant.util import slugify

from .config_flow import remove_photo
from .const import DOMAIN, LOGGER, PLATFORMS
from .coordinator import SimplePlantExtendedCoordinator
from .notification_manager import NotificationManager

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.typing import ConfigType


CONFIG_SCHEMA = config_entry_only_config_schema(DOMAIN)

SERVICE_ADD_NOTE = "add_note"
SERVICE_RELOAD = "reload"
SERVICE_CLEAR_LOGS = "clear_logs"
NOTE_LOG_KEY = "notes_log"
MAX_NOTES_LOG = 100
ACTIVITY_LOG_KEY = "activity_log"


async def _get_logbook_message(
    hass: HomeAssistant,
    action: str,
    *,
    old: str | None = None,
    new: str | None = None,
    note: str | None = None,
) -> str | None:
    language = hass.config.language
    cache = hass.data.setdefault(DOMAIN, {}).setdefault("_logbook_translations", {})
    translations = cache.get(language)
    if translations is None:
        translations = await async_get_translations(
            hass, language, "logbook", {DOMAIN}
        )
        cache[language] = translations

    key = f"{DOMAIN}.logbook.{action}"
    template = translations.get(key)
    if not template:
        return None

    return template.format(
        old=old or "",
        new=new or "",
        note=note or "",
    )


async def async_setup(hass: HomeAssistant, _config: ConfigType) -> bool:
    """Set up the Simple Plant component."""
    hass.data.setdefault(DOMAIN, {})

    async def async_state_changed(event: Event) -> None:
        entity_id = event.data.get("entity_id")
        if not entity_id or f"{DOMAIN}_" not in entity_id:
            return

        old_state = event.data.get("old_state")
        new_state = event.data.get("new_state")
        if not old_state or not new_state:
            return
        if old_state.state in {"unknown", "unavailable"}:
            return
        if new_state.state in {"unknown", "unavailable"}:
            return
        if not new_state.context or not new_state.context.user_id:
            return
        if old_state.state == new_state.state:
            return

        suffix = entity_id.split(f"{DOMAIN}_", 1)[1]
        if "_" not in suffix:
            return
        key, device = suffix.rsplit("_", 1)

        action_map = {
            "last_watered": "watered",
            "last_fertilized": "fertilized",
            "last_misted": "misted",
            "last_cleaned": "cleaned",
            "location": "location_changed",
            "size": "size_changed",
            "soil_type": "soil_type_changed",
            "feed_method": "feed_method_changed",
            "illumination": "illumination_changed",
            "health": "health_changed",
            "misting_enabled": "misting_setting_changed",
            "cleaning_enabled": "cleaning_setting_changed",
            "distance_to_window": "distance_to_window_changed",
            "pot_diameter": "pot_diameter_changed",
            "days_between_waterings": "watering_interval_changed",
            "days_between_fertilizations": "fertilization_interval_changed",
            "days_between_mistings": "misting_interval_changed",
            "days_between_cleanings": "cleaning_interval_changed",
            "notes": "notes_updated",
            "species": "species_updated",
            "picture": "image_updated",
        }

        action = action_map.get(key)
        if action is None:
            return

        coordinator: SimplePlantExtendedCoordinator | None = None
        for value in hass.data.get(DOMAIN, {}).values():
            if isinstance(value, SimplePlantExtendedCoordinator) and value.device == device:
                coordinator = value
                break
        if coordinator is None:
            return

        await coordinator.async_log_activity(
            action,
            entity_id=entity_id,
            old=old_state.state,
            new=new_state.state,
        )

        if key == "notes":
            skip_notes = hass.data.setdefault(DOMAIN, {}).setdefault("_notes_skip", {})
            if skip_notes.get(device) == new_state.state:
                skip_notes.pop(device, None)
            else:
                timestamp = datetime.now(timezone.utc).isoformat()
                current = await coordinator.store.async_get_data(coordinator.device)
                notes_log = list(current.get(NOTE_LOG_KEY, []))
                notes_log.append({"timestamp": timestamp, "note": new_state.state})
                if len(notes_log) > MAX_NOTES_LOG:
                    notes_log = notes_log[-MAX_NOTES_LOG:]
                await coordinator.store.async_save_data(
                    coordinator.device,
                    {NOTE_LOG_KEY: notes_log},
                )
                updated_data = await coordinator.store.async_get_data(coordinator.device)
                coordinator.async_set_updated_data(updated_data)

        message = await _get_logbook_message(
            hass,
            action,
            old=old_state.state,
            new=new_state.state,
        )
        if message is not None:
            async_log_entry(
                hass,
                DOMAIN,
                coordinator.config_entry.title,
                message,
                entity_id=entity_id,
            )

    async def async_add_note_service(call) -> None:  # type: ignore[no-untyped-def]
        entity_id = call.data.get("entity_id")
        note = call.data.get("note")
        if not entity_id or note is None:
            LOGGER.warning("add_note requires entity_id and note")
            return
        ent_reg = async_get(hass)
        entity_entry = ent_reg.async_get(entity_id)
        coordinator: SimplePlantExtendedCoordinator | None = None
        if entity_entry is not None:
            entry_id = entity_entry.config_entry_id
            coordinator = hass.data[DOMAIN].get(entry_id)
        if coordinator is None and f"{DOMAIN}_" in entity_id:
            suffix = entity_id.split(f"{DOMAIN}_", 1)[1]
            if "_" in suffix:
                _, device = suffix.rsplit("_", 1)
                for value in hass.data.get(DOMAIN, {}).values():
                    if (
                        isinstance(value, SimplePlantExtendedCoordinator)
                        and value.device == device
                    ):
                        coordinator = value
                        break
        if coordinator is None:
            LOGGER.warning("Coordinator not found for entity %s", entity_id)
            return

        timestamp = datetime.now(timezone.utc).isoformat()
        current = await coordinator.store.async_get_data(coordinator.device)
        notes_log = list(current.get(NOTE_LOG_KEY, []))
        notes_log.append({"timestamp": timestamp, "note": note})
        if len(notes_log) > MAX_NOTES_LOG:
            notes_log = notes_log[-MAX_NOTES_LOG:]

        await coordinator.store.async_save_data(
            coordinator.device,
            {NOTE_LOG_KEY: notes_log},
        )
        updated_data = await coordinator.store.async_get_data(coordinator.device)
        coordinator.async_set_updated_data(updated_data)

        notes_entity_id = f"text.{DOMAIN}_notes_{coordinator.device}"
        hass.data.setdefault(DOMAIN, {}).setdefault("_notes_skip", {})[
            coordinator.device
        ] = note
        await hass.services.async_call(
            "text",
            "set_value",
            {"entity_id": notes_entity_id, "value": note},
            blocking=True,
        )

        await coordinator.async_log_activity(
            "note_added",
            entity_id=entity_id,
            note=note,
        )

        hass.bus.async_fire(
            f"{DOMAIN}_note_added",
            {
                "device": coordinator.device,
                "note": note,
                "timestamp": timestamp,
            },
        )

        message = await _get_logbook_message(hass, "note_added", note=note)
        async_log_entry(
            hass,
            DOMAIN,
            coordinator.config_entry.title,
            message or f"Note added: {note}",
            entity_id=entity_id,
        )

    async def async_reload_service(call) -> None:  # type: ignore[no-untyped-def]
        entity_id = call.data.get("entity_id")
        if entity_id:
            ent_reg = async_get(hass)
            entity_entry = ent_reg.async_get(entity_id)
            if entity_entry is None:
                LOGGER.warning("Entity %s not found for reload", entity_id)
                return
            entry_id = entity_entry.config_entry_id
            await hass.config_entries.async_reload(entry_id)
            return

        for entry in hass.config_entries.async_entries(DOMAIN):
            await hass.config_entries.async_reload(entry.entry_id)

    async def async_clear_logs_service(call) -> None:  # type: ignore[no-untyped-def]
        period = call.data.get("period", "all")
        cutoff = None
        now = datetime.now(timezone.utc)
        if period == "3_months":
            cutoff = now - timedelta(days=90)
        elif period == "6_months":
            cutoff = now - timedelta(days=180)
        elif period == "1_year":
            cutoff = now - timedelta(days=365)

        for entry in hass.config_entries.async_entries(DOMAIN):
            coordinator: SimplePlantExtendedCoordinator | None = hass.data[DOMAIN].get(
                entry.entry_id
            )
            if coordinator is None:
                continue
            current = await coordinator.store.async_get_data(coordinator.device)

            def _filter_log(items: list[dict[str, str]] | None) -> list[dict[str, str]]:
                if not items or cutoff is None:
                    return [] if period == "all" else (items or [])
                filtered: list[dict[str, str]] = []
                for item in items:
                    timestamp = item.get("timestamp")
                    if not timestamp:
                        continue
                    try:
                        if datetime.fromisoformat(timestamp) >= cutoff:
                            filtered.append(item)
                    except ValueError:
                        continue
                return filtered

            notes_log = _filter_log(list(current.get(NOTE_LOG_KEY, [])))
            activity_log = _filter_log(list(current.get(ACTIVITY_LOG_KEY, [])))
            await coordinator.store.async_save_data(
                coordinator.device,
                {NOTE_LOG_KEY: notes_log, ACTIVITY_LOG_KEY: activity_log},
            )
            updated_data = await coordinator.store.async_get_data(coordinator.device)
            coordinator.async_set_updated_data(updated_data)

    # Start runtime notifications/broadcast manager
    manager = NotificationManager(hass)
    hass.data[DOMAIN]["notification_manager"] = manager
    await manager.async_start()

    hass.bus.async_listen(EVENT_STATE_CHANGED, async_state_changed)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD_NOTE,
        async_add_note_service,
        schema=vol.Schema(
            {
                vol.Required("entity_id"): cv.entity_id,
                vol.Required("note"): cv.string,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_RELOAD,
        async_reload_service,
        schema=vol.Schema(
            {
                vol.Optional("entity_id"): cv.entity_id,
            }
        ),
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_LOGS,
        async_clear_logs_service,
        schema=vol.Schema(
            {
                vol.Required("period"): vol.In(
                    ["3_months", "6_months", "1_year", "all"]
                )
            }
        ),
    )

    return True


# https://developers.home-assistant.io/docs/config_entries_index/#setting-up-an-entry
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    LOGGER.debug("Setting up entry %s", entry.title)
    if "fertilization_method" in entry.data and "feed_method" not in entry.data:
        data = dict(entry.data)
        data["feed_method"] = data.pop("fertilization_method")
        hass.config_entries.async_update_entry(entry, data=data)
    coordinator = SimplePlantExtendedCoordinator(hass, entry)
    await coordinator.store.async_rename_key(
        coordinator.device,
        "fertilization_method",
        "feed_method",
    )
    if "feed_method" in entry.data:
        await hass.services.async_call(
            "select",
            "select_option",
            {
                "entity_id": f"select.{DOMAIN}_feed_method_{coordinator.device}",
                "option": entry.data["feed_method"],
            },
            blocking=True,
        )

    if entry.state == ConfigEntryState.SETUP_IN_PROGRESS:
        await coordinator.async_config_entry_first_refresh()
    else:
        await coordinator.async_request_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    entry.async_on_unload(
        hass.bus.async_listen(
            EVENT_DEVICE_REGISTRY_UPDATED,  # type: ignore[arg-type]
            on_device_registry_update_handler,
        )
    )

    manager: NotificationManager | None = hass.data[DOMAIN].get("notification_manager")
    if manager is not None:
        await manager.async_refresh()

    return True


async def on_device_registry_update_handler(
    event: Event[EventDeviceRegistryUpdatedData],
) -> None:
    """Handle update of device registry."""
    changes = event.data.get("changes")
    if not changes or not isinstance(changes, dict) or "name_by_user" not in changes:
        return
    # Get device
    hass = async_get_hass()
    device_registry = async_get(hass)
    device = device_registry.async_get(event.data.get("device_id"))
    if not device:
        return
    # Get entries
    entries: set[ConfigEntry] = set()
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry:
            entries.add(entry)
    # Update entries
    for entry in entries:
        device_name_from_entry_title = entry.title[0].upper() + entry.title[1:]
        if (
            device_name_from_entry_title == device.name_by_user
            or device.name_by_user is None
        ):
            return
        LOGGER.debug(
            "Renaming entry %s to %s",
            entry.title,
            device.name_by_user,
        )
        data = dict(entry.data)
        data.update(
            {
                "name": device.name_by_user,
                "name_by_user": device.name_by_user,
            }
        )
        new_title = device.name_by_user

        coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_rename_device(slugify(new_title))

        await hass.config_entries.async_unload(entry.entry_id)
        hass.config_entries.async_update_entry(entry, data=data, title=new_title)
        hass.config_entries.async_schedule_reload(entry.entry_id)
        device_registry.async_remove_device(device.id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Handle unloading of an entry."""
    # Unload platforms
    LOGGER.debug("Unloading %s", entry.title)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    LOGGER.debug("Unloading status : %s", "OK" if unload_ok else "NOK")

    # Remove entry data
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

        manager: NotificationManager | None = hass.data[DOMAIN].get(
            "notification_manager"
        )
        if manager is not None:
            await manager.async_refresh()

    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    # Remove storage
    coordinator = SimplePlantExtendedCoordinator(hass, entry)
    await coordinator.remove_device_from_storage()

    # Remove photo
    remove_photo(hass, entry)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> None:
    """Reload config entry."""
    if entry.title != entry.data.get("name"):
        LOGGER.info("Changing name of %s to %s", entry.data.get("name"), entry.title)
        # Migrate storage storage
        coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][entry.entry_id]
        await coordinator.async_rename_device(slugify(entry.title))
        # Update entry
        data = dict(entry.data)
        data.update({"name": entry.title, "name_by_user": entry.title})
        hass.config_entries.async_update_entry(entry, data=data)
        # remove obsolete device
        device_name = entry.title[0].upper() + entry.title[1:]
        device_registry = async_get(hass)
        for device in async_entries_for_config_entry(device_registry, entry.entry_id):
            if device.name != device_name:
                device_registry.async_remove_device(device.id)
        return
    LOGGER.info("Reloading entry %s", entry.title)
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)

    manager: NotificationManager | None = hass.data[DOMAIN].get("notification_manager")
    if manager is not None:
        await manager.async_refresh()
