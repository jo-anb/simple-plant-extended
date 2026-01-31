"""Adds config flow for Simple PLant Extended."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import voluptuous as vol
from homeassistant.components.file_upload import process_uploaded_file
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.util import slugify
from homeassistant.util.dt import as_local, as_utc, utcnow

from .const import (
    CONF_BROADCAST_ENABLED,
    CONF_BROADCAST_SERVICES,
    CONF_BROADCAST_TIME_1,
    CONF_BROADCAST_TIME_2,
    CONF_DND_END,
    CONF_DND_START,
    CONF_NOTIFICATIONS_ENABLED,
    CONF_NOTIFY_SERVICES,
    DEFAULT_BROADCAST_ENABLED,
    DEFAULT_BROADCAST_SERVICES,
    DEFAULT_BROADCAST_TIME_1,
    DEFAULT_BROADCAST_TIME_2,
    DEFAULT_DND_END,
    DEFAULT_DND_START,
    DEFAULT_NOTIFICATIONS_ENABLED,
    DOMAIN,
    ENABLED_OPTIONS,
    FEED_OPTIONS,
    HEALTH_OPTIONS,
    ILLUMINATION_OPTIONS,
    IMAGES_MIME_TYPES,
    LOCATION_OPTIONS,
    LOGGER,
    SIZE_OPTIONS,
    SOIL_TYPE_OPTIONS,
    STORAGE_DIR,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

## UTILS


async def save_image(hass: HomeAssistant, file_id: str) -> str:
    """Permanently save an uploaded image."""
    with process_uploaded_file(hass, file_id) as uploaded_file:
        # Save the file
        storage_dir = Path(hass.config.path(STORAGE_DIR))
        storage_dir.mkdir(parents=True, exist_ok=True)

        suffix = uploaded_file.suffix
        if suffix not in IMAGES_MIME_TYPES:
            raise ValueError
        file_path = storage_dir / f"{file_id}{suffix}"

        # Safely copy the file using async operations
        async with aiofiles.open(file_path, "wb") as destination_file:  # noqa: SIM117
            async with aiofiles.open(uploaded_file, "rb") as source_file:
                await destination_file.write(await source_file.read())

        # relative path
        return f"/{STORAGE_DIR}/{file_path.name}"


def remove_photo(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Remove the photo file of a config entry."""
    try:
        # Get the photo path from the entry's data
        photo_path = entry.data.get("photo")
        if photo_path:
            # Convert url path to actual file path
            file_path = Path(str(hass.config.path(photo_path.lstrip("/"))))

            LOGGER.info("Trying to remove: %s", photo_path)

            # Check if file exists before trying to remove it
            if file_path.exists():
                file_path.unlink()
                LOGGER.info("Successfully removed image file: %s", file_path)
            else:
                LOGGER.warning("Image file not found: %s", file_path)
    except OSError as err:
        LOGGER.error("Error reading image file %s: %s", file_path, err)


## CONFIG FLOW SCHEMAS


def user_form() -> vol.Schema:
    """Return a new device form."""
    LOGGER.debug("config_flow, 1st call : displaying form")
    return vol.Schema(
        {
            vol.Required("name"): selector.TextSelector(
                selector.TextSelectorConfig(multiline=False, multiple=False)
            ),
            vol.Required("last_watered"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Required("days_between_waterings"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=360,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Required("feed_method"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": FEED_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Required("last_fertilized"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Required("days_between_fertilizations"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=360,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Required("misting_enabled"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": ENABLED_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Required("last_misted"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Optional("days_between_mistings"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=360,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Required("last_cleaned"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Required("cleaning_enabled"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": ENABLED_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("days_between_cleanings"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1,
                    max=360,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="days",
                ),
            ),
            vol.Required("illumination"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": ILLUMINATION_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Required("health"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": HEALTH_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("species", default="notset"): selector.TextSelector(
                selector.TextSelectorConfig(multiline=False, multiple=False)
            ),
            vol.Optional("size", default="notset"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": SIZE_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("location", default="notset"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": LOCATION_OPTIONS,
                        "custom_value": True,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("distance_to_window"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=1000,
                    step=10,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="cm",
                )
            ),
            vol.Optional("pot_diameter"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=200,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="cm",
                )
            ),
            vol.Optional("soil_type", default="notset"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": SOIL_TYPE_OPTIONS,
                        "custom_value": True,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("acquisition_date"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Optional("humidity_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="humidity",
                )
            ),
            vol.Optional("temperature_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            ),
            vol.Optional("light_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="illuminance",
                )
            ),
            vol.Optional("notes"): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True, multiple=False)
            ),
            vol.Required("photo"): selector.FileSelector(
                selector.FileSelectorConfig(accept="image/*")
            ),
        }
    )


def option_form(suggested_species: str | None = None) -> vol.Schema:
    """Return a device reconfiguration form."""
    LOGGER.debug("option_flow, 1st call : displaying form")
    return vol.Schema(
        {
            vol.Optional("species", default="", description=suggested_species): str,
            vol.Optional("size"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": SIZE_OPTIONS,
                        "custom_value": False,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("location"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": LOCATION_OPTIONS,
                        "custom_value": True,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("distance_to_window"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0,
                    max=1000,
                    step=10,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="cm",
                )
            ),
            vol.Optional("pot_diameter"): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=5,
                    max=200,
                    step=1,
                    mode=selector.NumberSelectorMode.BOX,
                    unit_of_measurement="cm",
                )
            ),
            vol.Optional("soil_type"): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    {
                        "options": SOIL_TYPE_OPTIONS,
                        "custom_value": True,
                        "sort": False,
                    }
                )
            ),
            vol.Optional("acquisition_date"): selector.DateSelector(
                selector.DateSelectorConfig(),
            ),
            vol.Optional("humidity_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="humidity",
                )
            ),
            vol.Optional("temperature_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="temperature",
                )
            ),
            vol.Optional("light_sensor"): selector.EntitySelector(
                selector.EntitySelectorConfig(
                    domain="sensor",
                    device_class="illuminance",
                )
            ),
            vol.Optional("notes"): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True, multiple=False)
            ),
            vol.Optional("photo"): selector.FileSelector(
                selector.FileSelectorConfig(accept="image/*")
            ),
        }
    )


def notification_options_form(
    available_notify_services: list[str],
    selected_notify_services: list[str],
    *,
    notifications_enabled: bool,
    dnd_start: str,
    dnd_end: str,
) -> vol.Schema:
    """Return notification options form (integration-level)."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_NOTIFY_SERVICES, default=selected_notify_services
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=available_notify_services,
                    custom_value=True,
                    multiple=True,
                )
            ),
            vol.Optional(
                CONF_NOTIFICATIONS_ENABLED, default=notifications_enabled
            ): selector.BooleanSelector(),
            vol.Optional(CONF_DND_START, default=dnd_start): selector.TimeSelector(
                selector.TimeSelectorConfig()
            ),
            vol.Optional(CONF_DND_END, default=dnd_end): selector.TimeSelector(
                selector.TimeSelectorConfig()
            ),
        }
    )


def broadcast_options_form(
    available_broadcast_services: list[str],
    selected_broadcast_services: list[str],
    *,
    broadcast_enabled: bool,
    time_1: str,
    time_2: str,
) -> vol.Schema:
    """Return broadcast options form (integration-level)."""
    return vol.Schema(
        {
            vol.Optional(
                CONF_BROADCAST_ENABLED, default=broadcast_enabled
            ): selector.BooleanSelector(),
            vol.Optional(
                CONF_BROADCAST_SERVICES, default=selected_broadcast_services
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=available_broadcast_services,
                    custom_value=True,
                    multiple=True,
                )
            ),
            vol.Optional(CONF_BROADCAST_TIME_1, default=time_1): selector.TimeSelector(
                selector.TimeSelectorConfig()
            ),
            vol.Optional(CONF_BROADCAST_TIME_2, default=time_2): selector.TimeSelector(
                selector.TimeSelectorConfig()
            ),
        }
    )


## CONFIG FLOWS


class SimplePlantExtendedFlowHandler(ConfigFlow, domain=DOMAIN):
    """Config flow for Simple Plant Extended."""

    def __init__(self) -> None:
        """Init."""
        self._user_inputs: dict = {}

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get options flow for this handler."""
        return SimplePlantExtendedOptionFlowHandler(config_entry)

    async def async_step_user(self, user_input: dict | None = None) -> ConfigFlowResult:
        """
        Provide Base Plant information Config Flow.

        1st call = return form to show
        2nd call = return form with user input
        """
        if user_input is None:
            # 1st call
            return self.async_show_form(step_id="user", data_schema=user_form())
        # 2nd call
        # Verify name
        domain_entries = self.hass.config_entries.async_entries(domain=DOMAIN)
        domain_entries_title_slugs = [slugify(entry.title) for entry in domain_entries]
        LOGGER.debug(domain_entries_title_slugs)
        if slugify(user_input["name"]) in domain_entries_title_slugs:
            return self.async_show_form(
                step_id="user",
                data_schema=user_form(),
                errors={"base": "name_exist"},
            )
        user_input["name_by_user"] = user_input["name"]
        # Verify date
        if "last_watered" in user_input:
            date = as_utc(as_local(datetime.fromisoformat(user_input["last_watered"])))
            if date > utcnow():
                return self.async_show_form(
                    step_id="user",
                    data_schema=user_form(),
                    errors={"base": "invalid_future_date"},
                )
        if "photo" not in user_input:
            return self.async_show_form(
                step_id="user",
                errors={"base": "upload_failed_generic"},
            )
        file_id = user_input["photo"]

        try:
            user_input["photo"] = await save_image(self.hass, file_id)
        except ValueError:
            return self.async_show_form(
                step_id="user",
                errors={"base": "upload_failed_type"},
            )

        return self.async_create_entry(title=user_input["name"], data=user_input)


class SimplePlantExtendedOptionFlowHandler(OptionsFlow):
    """Reconfiguration flow for Simple Plant Extended."""

    def __init__(self, entry: ConfigEntry) -> None:
        """Init."""
        self.user_inputs: dict = {}
        self.entry = entry

    async def async_step_init(self, user_input: dict | None = None) -> ConfigFlowResult:
        """
        Provide new information.

        1st call = return form to show
        2nd call = return form with user input
        """
        available_notify_services = self._get_notify_services_options()
        current_options = self._get_current_notification_options()
        available_broadcast_services = self._get_broadcast_services_options(
            available_notify_services
        )

        form = vol.Schema(
            {
                **option_form(self.entry.data.get("species")).schema,
                **notification_options_form(
                    available_notify_services=available_notify_services,
                    selected_notify_services=current_options[CONF_NOTIFY_SERVICES],
                    notifications_enabled=current_options[CONF_NOTIFICATIONS_ENABLED],
                    dnd_start=current_options[CONF_DND_START],
                    dnd_end=current_options[CONF_DND_END],
                ).schema,
                **broadcast_options_form(
                    available_broadcast_services=available_broadcast_services,
                    selected_broadcast_services=current_options[
                        CONF_BROADCAST_SERVICES
                    ],
                    broadcast_enabled=current_options[CONF_BROADCAST_ENABLED],
                    time_1=current_options[CONF_BROADCAST_TIME_1],
                    time_2=current_options[CONF_BROADCAST_TIME_2],
                ).schema,
            }
        )

        if user_input is None:
            # 1st call
            return self.async_show_form(step_id="init", data_schema=form)
        # 2nd call
        if user_input.get("species"):
            self.user_inputs["species"] = user_input["species"]

        for key in (
            "size",
            "location",
            "distance_to_window",
            "pot_diameter",
            "soil_type",
            "acquisition_date",
            "humidity_sensor",
            "temperature_sensor",
            "light_sensor",
            "notes",
        ):
            if key in user_input:
                self.user_inputs[key] = user_input[key]

        if user_input.get("photo"):
            try:
                file_id = user_input["photo"]
                self.user_inputs["photo"] = await save_image(self.hass, file_id)
                remove_photo(self.hass, self.entry)
            except ValueError:
                return self.async_show_form(
                    step_id="user",
                    errors={"base": "upload_failed_type"},
                )

        if CONF_NOTIFY_SERVICES in user_input:
            self.user_inputs[CONF_NOTIFY_SERVICES] = user_input[CONF_NOTIFY_SERVICES]

        if CONF_NOTIFICATIONS_ENABLED in user_input:
            self.user_inputs[CONF_NOTIFICATIONS_ENABLED] = user_input[
                CONF_NOTIFICATIONS_ENABLED
            ]

        if CONF_DND_START in user_input:
            self.user_inputs[CONF_DND_START] = user_input[CONF_DND_START]

        if CONF_DND_END in user_input:
            self.user_inputs[CONF_DND_END] = user_input[CONF_DND_END]

        if CONF_BROADCAST_ENABLED in user_input:
            self.user_inputs[CONF_BROADCAST_ENABLED] = user_input[
                CONF_BROADCAST_ENABLED
            ]

        if CONF_BROADCAST_SERVICES in user_input:
            self.user_inputs[CONF_BROADCAST_SERVICES] = user_input[
                CONF_BROADCAST_SERVICES
            ]

        if CONF_BROADCAST_TIME_1 in user_input:
            self.user_inputs[CONF_BROADCAST_TIME_1] = user_input[CONF_BROADCAST_TIME_1]

        if CONF_BROADCAST_TIME_2 in user_input:
            self.user_inputs[CONF_BROADCAST_TIME_2] = user_input[CONF_BROADCAST_TIME_2]

        # On appelle le step de fin pour enregistrer les modifications
        return await self.async_end()

    async def async_end(self) -> ConfigFlowResult:
        """Finitsh ConfigEntry modification."""
        LOGGER.info(
            "Entry %s is being recreated",
            self.config_entry.entry_id,
        )

        data = dict(self.config_entry.data)
        options = dict(self.config_entry.options)

        for key in (
            "species",
            "photo",
            "size",
            "location",
            "distance_to_window",
            "pot_diameter",
            "soil_type",
            "acquisition_date",
            "humidity_sensor",
            "temperature_sensor",
            "light_sensor",
            "notes",
        ):
            if key in self.user_inputs:
                data[key] = self.user_inputs[key]

        for key in (
            CONF_NOTIFY_SERVICES,
            CONF_NOTIFICATIONS_ENABLED,
            CONF_DND_START,
            CONF_DND_END,
            CONF_BROADCAST_ENABLED,
            CONF_BROADCAST_SERVICES,
            CONF_BROADCAST_TIME_1,
            CONF_BROADCAST_TIME_2,
        ):
            if key in self.user_inputs:
                options[key] = self.user_inputs[key]

        self.hass.config_entries.async_update_entry(
            self.config_entry, data=data, options=options
        )

        # Propagate notification settings to all entries (integration-level)
        for entry in self.hass.config_entries.async_entries(domain=DOMAIN):
            if entry.entry_id == self.config_entry.entry_id:
                continue
            self.hass.config_entries.async_update_entry(entry, options=options)

        manager = self.hass.data.get(DOMAIN, {}).get("notification_manager")
        if manager is not None:
            await manager.async_refresh()

        return self.async_create_entry(
            # No data as config entry has been modified
            title=None,
            data={},
        )

    def _get_notify_services_options(self) -> list[str]:
        """Get list of available notify services with full service names."""
        services = self.hass.services.async_services().get("notify", {})
        service_names = sorted(services.keys())
        return [f"notify.{name}" for name in service_names]

    def _get_broadcast_services_options(self, notify_services: list[str]) -> list[str]:
        """
        Get list of available broadcast services.

        For now, use notify services (e.g. notify.google_assistant_sdk). This keeps
        the integration extensible for future broadcast providers.
        """
        return notify_services

    def _get_current_notification_options(self) -> dict:
        """Get current notification options with defaults."""
        return {
            CONF_NOTIFY_SERVICES: self.entry.options.get(CONF_NOTIFY_SERVICES, []),
            CONF_NOTIFICATIONS_ENABLED: self.entry.options.get(
                CONF_NOTIFICATIONS_ENABLED, DEFAULT_NOTIFICATIONS_ENABLED
            ),
            CONF_DND_START: self.entry.options.get(CONF_DND_START, DEFAULT_DND_START),
            CONF_DND_END: self.entry.options.get(CONF_DND_END, DEFAULT_DND_END),
            CONF_BROADCAST_ENABLED: self.entry.options.get(
                CONF_BROADCAST_ENABLED, DEFAULT_BROADCAST_ENABLED
            ),
            CONF_BROADCAST_SERVICES: self.entry.options.get(
                CONF_BROADCAST_SERVICES, DEFAULT_BROADCAST_SERVICES
            ),
            CONF_BROADCAST_TIME_1: self.entry.options.get(
                CONF_BROADCAST_TIME_1, DEFAULT_BROADCAST_TIME_1
            ),
            CONF_BROADCAST_TIME_2: self.entry.options.get(
                CONF_BROADCAST_TIME_2, DEFAULT_BROADCAST_TIME_2
            ),
        }
