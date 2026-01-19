"""Data coordinator for simple_plant_extended."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import (
    HomeAssistantError,
    ServiceNotFoundError,
    ServiceValidationError,
)
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.util import slugify
from homeassistant.util.dt import as_local, as_utc, utcnow

from .const import DOMAIN, LOGGER, MANUFACTURER
from .data import SimplePlantExtendedStore

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant


class SimplePlantExtendedCoordinator(DataUpdateCoordinator[dict]):
    """Class to manage fetching Simple Plant Extended data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
        )
        self.device = slugify(entry.title)
        self.store = SimplePlantExtendedStore(hass)
        self.config_entry = entry

        # Set up device info
        name = entry.title[0].upper() + entry.title[1:]
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, f"{DOMAIN}_{self.device}")},
            name=name,
            manufacturer=MANUFACTURER,
            model=entry.data.get("species"),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from storage."""
        await self.store.async_load()
        return await self.store.async_get_data(self.device)

    async def remove_device_from_storage(self) -> None:
        """Remove entry in storage."""
        await self.store.async_remove_device(self.device)
        await self.async_refresh()

    async def async_store_value(self, entity_id: str, value: str) -> None:
        """Store value in the store."""
        await self.store.async_save_data(self.device, {entity_id: value})
        await self.async_refresh()

    async def async_rename_device(self, new_id: str) -> None:
        """Migrate data for a device to another name."""
        await self.store.async_rename_device(self.device, new_id)
        await self.async_refresh()

    async def async_set_last_action_date(self, value: datetime, action: str) -> None:
        """Change last action date manually."""
        new_value = as_utc(value)
        if new_value > utcnow():
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="invalid_future_date",
                translation_placeholders={},
            )
        await self.store.async_save_data(
            self.device, {f"{action}": new_value.isoformat()}
        )
        await self.async_refresh()

    async def async_mark_action_toggle(self, action: str) -> None:
        """Toggle last action between old value and today."""
        data = await self.store.async_get_data(self.device)
        if data is None:
            LOGGER.warning("%s: No data found in storage", self.device)
            return

        last_action = None
        old_last_action = None
        if f"last_{action}" in data:
            last_action = as_utc(
                as_local(datetime.fromisoformat(data[f"last_{action}"]))
            )
        if f"_old_last_{action}" in data:
            old_last_action = as_utc(
                as_local(datetime.fromisoformat(data[f"_old_last_{action}"]))
            )

        if last_action and as_local(last_action).date() != as_local(utcnow()).date():
            await self.async_action_mark_action(save_old=last_action, action=action)
        else:
            await self.async_action_cancel_mark_action(
                old_value=old_last_action, action=action
            )

    async def async_action_cancel_mark_action(
        self, old_value: datetime | None = None, action: str = "watered"
    ) -> None:
        """Update last action date to old value."""
        if old_value:
            await self.async_set_last_action_date(
                as_utc(old_value), action=f"last_{action}"
            )
        else:
            await self.async_action_mark_action(action=action)

    async def async_action_mark_action(
        self, save_old: datetime | None = None, action: str = "watered"
    ) -> None:
        """Update last action date today."""
        today = utcnow()
        if save_old:
            await self.store.async_save_data(
                self.device, {f"_old_last_{action}": as_utc(save_old).isoformat()}
            )
        await self.async_set_last_action_date(today, f"last_{action}")

    async def get_dates(self) -> dict[str, datetime] | None:
        """Get dates from relevant device entity states, with retry."""
        states_to_get = {
            "last_watered": f"date.{DOMAIN}_last_watered_{self.device}",
            "nb_watered_days": f"number.{DOMAIN}_days_between_waterings_{self.device}",
            "last_feed": f"sensor.{DOMAIN}_feed_lastfeed_{self.device}",
            "last_fertilized": f"date.{DOMAIN}_last_fertilized_{self.device}",
            "nb_fertilized_days": f"number.{DOMAIN}_days_between_fertilizations_{self.device}",
            "last_misted": f"date.{DOMAIN}_last_misted_{self.device}",
            "nb_misted_days": f"number.{DOMAIN}_days_between_mistings_{self.device}",
            "last_cleaned": f"date.{DOMAIN}_last_cleaned_{self.device}",
            "nb_cleaned_days": f"number.{DOMAIN}_days_between_cleanings_{self.device}",
        }

        for attempt in range(5):
            data = {
                key: self.hass.states.get(eid) for key, eid in states_to_get.items()
            }

            if all(
                data[key] is not None
                and data[key].state not in (None, "", "unknown", "unavailable")
                for key in states_to_get
            ):
                break

            LOGGER.info(
                "%s: Waiting for entity states... (%d)", self.device, attempt + 1
            )
            await asyncio.sleep(2)
        else:
            LOGGER.warning("%s: Couldn't get all states after retry", self.device)
            # return None

        states = {key: data[key].state for key in data if data[key] is not None}

        try:
            last_watered_date = datetime.fromisoformat(states["last_watered"])
            nb_watered_days = float(states["nb_watered_days"])

            last_fertilized_date = datetime.fromisoformat("1970-01-01")
            if states["last_fertilized"] not in ["unknown", "", "None"]:
                last_fertilized_date = datetime.fromisoformat(states["last_fertilized"])
            nb_fertilized_days = (
                float(states["nb_fertilized_days"])
                if float(states["nb_fertilized_days"]) > 0
                else 1
            )

            last_misted_date = datetime.fromisoformat("1970-01-01")
            if states["last_misted"] not in ["unknown", "", "None"]:
                last_misted_date = datetime.fromisoformat(states["last_misted"])
            nb_misted_days = (
                float(states["nb_misted_days"])
                if float(states["nb_misted_days"]) > 0
                else 1
            )

            last_cleaned_date = datetime.fromisoformat("1970-01-01")
            if states["last_cleaned"] not in ["unknown", "", "None"]:
                last_cleaned_date = datetime.fromisoformat(states["last_cleaned"])
            nb_cleaned_days = (
                float(states["nb_cleaned_days"])
                if float(states["nb_cleaned_days"]) > 0
                else 1
            )

            return {
                "last_watered": last_watered_date,
                "next_watering": last_watered_date + timedelta(days=nb_watered_days),
                "last_fertilized": last_fertilized_date,
                "next_fertilization": last_fertilized_date
                + timedelta(days=nb_fertilized_days),
                "last_misted": last_misted_date,
                "next_misting": last_misted_date + timedelta(days=nb_misted_days),
                "last_cleaned": last_cleaned_date,
                "next_cleaning": last_cleaned_date + timedelta(days=nb_cleaned_days),
                "today": utcnow(),
            }
        except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
            LOGGER.warning("%s: Failed to parse dates: %s", self.device, e)
            return None

    # async def async_migrate_data(self) -> None:
    #     """Migrate data for a device to another name."""
    #     states_to_get = {
    #         "migrate_last_feed_date": f"sensor.{DOMAIN}_feed_lastfeed_{self.device}",
    #         "feed_method": f"input_select.{DOMAIN}_feed_method_{self.device}",
    #         "feed_interval": f"input_number.{DOMAIN}_feed_interval_{self.device}",
    #         "misting_enabled": f"binary_sensor.{DOMAIN}_care_misting_enabled_{self.device}",
    #         "misting_interval": f"input_number.{DOMAIN}_care_mist_interval_{self.device}",
    #         "cleaning_enabled": f"binary_sensor.{DOMAIN}_care_cleaning_enabled_{self.device}",
    #         "cleaning_interval": f"input_number.{DOMAIN}_care_clean_interval_{self.device}",
    #         "next_misting": f"sensor.{DOMAIN}_care_next_misting_{self.device}",
    #         "next_cleaning": f"sensor.{DOMAIN}_care_next_cleaning_{self.device}",
    #     }

    #     # Get states from hass
    #     data = {key: self.hass.states.get(eid) for key, eid in states_to_get.items()}

    #     # Check if all states are available
    #     if any(
    #         data[key] is None
    #         or not data[key].state  # type: ignore noqa: PGH003
    #         or data[key].state == "unavailable"  # type: ignore noqa: PGH003
    #         for key in states_to_get
    #     ):

    #         return

    #     states = {key: data.state for key, data in data.items() if data is not None}
    #     response = {
    #         "status": "success",
    #         "data": states,
    #     }

    #     feed_actions = ["feed"]
    #     for action in feed_actions:
    #         last_action = states["migrate_last_feed_date"]
    #         method = states["feed_method"]
    #         interval = float(states["feed_interval"])
    #         response["feed"] = { "message": f"{self.device} migrating feed data"}

    #         if last_action not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 dt = datetime.fromisoformat(str(last_action))
    #                 iso_date = dt.date().isoformat()

    #                 response["feed"]["last_action"] = await self.store.async_save_data(
    #                     self.device,
    #                     {"last_fertilized": iso_date},
    #                 )

    #                 iso_next_date = (dt + timedelta(days=round(interval))).date().isoformat()

    #                 response["feed"]["next_date"] = await self.store.async_save_data(
    #                     self.device,
    #                     {"next_fertilization": iso_next_date},
    #                 )

    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to convert feed date: %s", self.device, response)
    #         else:
    #             response["feed"]["last_action"] = {"message": "No last feed date to migrate"}

    #         if method not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 feed_method_store = await self.store.async_save_data(
    #                     self.device,
    #                     {"feed_method": method},
    #                 )

    #                 feed_method__sync = await self.hass.services.async_call(
    #                     "select",
    #                     "select_option",
    #                     {
    #                         "entity_id": f"select.{DOMAIN}_feed_method_{self.device}",
    #                         "option": method,
    #                     },
    #                     blocking=True,
    #                 )
    #                 response["feed"]["method"] = f"{feed_method_store} \n {feed_method__sync}"

    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to migrate feed method: %s", self.device, response)
    #         else:
    #             response["feed"]["method"] = {"message": "No feed method to migrate"}

    #         if interval not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 interval_store = await self.store.async_save_data(
    #                     self.device,
    #                     {"days_between_fertilizations": interval},
    #                 )
    #                 interval_sync = await self.hass.services.async_call(
    #                     "number",
    #                     "set_value",
    #                     {
    #                         "entity_id": f"number.{DOMAIN}_days_between_fertilizations_{self.device}",
    #                         "value": interval,
    #                     },
    #                     blocking=True,
    #                 )
    #                 response["feed"]["interval"] = f"{interval_store} \n {interval_sync}"
    #                 # await self.async_set_last_action_date(iso_date, "last_fertilized")

    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to migrate feed interval: %s", self.device, response)
    #         else:
    #             response["feed"]["interval"] = {"message": "No feed interval to migrate"}

    #     care_actions = ["misting", "cleaning"]
    #     for action in care_actions:
    #         enabled = states[f"{action}_enabled"]
    #         interval = float(states[f"{action}_interval"])
    #         next_action = states[f"next_{action}"]
    #         response[f"{action}"] = {"message": f"{self.device} migrating care data"}

    #         if enabled not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 enabled_store = await self.store.async_save_data(
    #                     self.device,
    #                     {f"{action}_enabled": enabled},
    #                 )

    #                 enabled_sync = await self.hass.services.async_call(
    #                     "select",
    #                     "select_option",
    #                     {
    #                         "entity_id": f"select.{DOMAIN}_{action}_enabled_{self.device}",
    #                         "option": enabled,
    #                     },
    #                     blocking=True,
    #                 )
    #                 response[f"{action}"]["enabled"] = f"{enabled_store} \n {enabled_sync}"
    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to migrate %s enabled: %s", self.device, action, response)
    #         else:
    #             response[f"{action}"]["enabled"] = {"message": "No enabled state to migrate"}

    #         if interval not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 interval_store = await self.store.async_save_data(
    #                     self.device,
    #                     {f"days_between_{action}s": interval},
    #                 )
    #                 interval_sync = await self.hass.services.async_call(
    #                     "number",
    #                     "set_value",
    #                     {
    #                         "entity_id": f"number.{DOMAIN}_days_between_{action}s_{self.device}",
    #                         "value": interval,
    #                     },
    #                     blocking=True,
    #                 )
    #                 response[f"{action}"]["interval"] = f"{interval_store} \n {interval_sync}"
    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to migrate %s interval: %s", self.device, action, response)
    #         else:
    #             response[f"{action}"]["interval"] = {"message": "No interval state to migrate"}

    #         if next_action not in [None, "None", "unknown", "unavailable"]:
    #             try:
    #                 dt = datetime.fromisoformat(str(next_action))
    #                 iso_date = (dt - timedelta(days=round(interval))).date().isoformat()
    #                 action_type = "cleaned" if action == "cleaning" else "misted"

    #                 response[f"{action}"]["next_date"] = await self.store.async_save_data(
    #                     self.device,
    #                     {f"last_{action_type}": iso_date},
    #                 )
    #             except (ServiceNotFoundError, ServiceValidationError, HomeAssistantError) as e:
    #                 response["status"] = "error"
    #                 response["error"] = str(e)
    #                 LOGGER.error("%s: Failed to migrate last %s date: %s", self.device, action, response)
    #         else:
    #             response[f"{action}"]["next_date"] = {"message": "No last date state to migrate"}
    #     await self.async_refresh()
    #     LOGGER.warning("%s: Finished Migrating data:\n\n %s", self.device, response)
