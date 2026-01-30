"""Select platform for simple_plant_extended."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.select import (
    SelectEntity,
    SelectEntityDescription,
)

from .const import (
    DOMAIN,
    ENABLED_OPTIONS,
    FEED_OPTIONS,
    HEALTH_OPTIONS,
    ILLUMINATION_OPTIONS,
    LOGGER,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


ENTITY_DESCRIPTIONS = (
    SelectEntityDescription(
        key="health",
        translation_key="health",
        icon="mdi:heart-pulse",
        options=HEALTH_OPTIONS,
    ),
    SelectEntityDescription(
        key="feed_method",
        translation_key="feed_method",
        icon="mdi:seed",
        options=FEED_OPTIONS,
    ),
    SelectEntityDescription(
        key="misting_enabled",
        translation_key="misting_enabled",
        icon="mdi:spray-bottle",
        options=ENABLED_OPTIONS,
    ),
    SelectEntityDescription(
        key="cleaning_enabled",
        translation_key="cleaning_enabled",
        icon="mdi:shimmer",
        options=ENABLED_OPTIONS,
    ),
    SelectEntityDescription(
        key="illumination",
        translation_key="illumination",
        icon="mdi:theme-light-dark",
        options=ILLUMINATION_OPTIONS,
    ),
)

COLOR_MAPPING = {
    "poor": "Tomato",
    "fair": "Yellow",
    "good": "GreenYellow",
    "verygood": "LawnGreen",
    "excellent": "LimeGreen",
    "on": "LawnGreen",
    "off": "DimGray",
    "sunny": "GoldenRod",
    "partly_sunny": "DarkGoldenRod",
    "shade": "DarkGray",
    "notset": "DimGray",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the select platform."""
    async_add_entities(
        SimplePlantExtendedSelect(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantExtendedSelect(SelectEntity):
    """simple_plant_extended select class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SelectEntityDescription,
    ) -> None:
        """Initialize the select class."""
        super().__init__()
        self.entity_description = description
        self._fallback_value = str(entry.data.get(description.key, "notset"))
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        device = self.coordinator.device

        self.entity_id = f"select.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        self._attr_extra_state_attributes = {
            "state_color": False,
        }

        # Set up device info
        self._attr_device_info = self.coordinator.device_info

    @property
    def device(self) -> str | None:
        """Return the device name."""
        return self.coordinator.device

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""

        async def _select_updated(event: Event, new_value: str | None = None) -> None:
            if self.entity_description.key in ["cleaning_enabled", "misting_enabled"]:
                subject = None
                if self.entity_description.key == "misting_enabled":
                    subject = "misting"
                    subject_short = "mist"
                elif self.entity_description.key == "cleaning_enabled":
                    subject = "cleaning"
                    subject_short = "clean"

                if new_value is not None:
                    new_state = new_value
                else:
                    new_state_obj = event.data.get("new_state")
                    new_state = new_state_obj.state if new_state_obj else None

                if new_state == "on":
                    await self.hass.services.async_call(
                        "homeassistant",
                        "turn_on",
                        {
                            "entity_id": [
                                f"button.{DOMAIN}_mark_{subject_short}ed_{self.device}",
                                f"date.{DOMAIN}_last_{subject_short}ed_{self.device}",
                                f"number.{DOMAIN}_days_between_{subject}s_{self.device}",
                                f"binary_sensor.{DOMAIN}_{subject}_problem_{self.device}",
                                f"binary_sensor.{DOMAIN}_{subject}_todo_{self.device}",
                                f"sensor.{DOMAIN}_next_{subject}_{self.device}",
                            ]
                        },
                        blocking=True,
                    )
                elif new_state == "off":
                    await self.hass.services.async_call(
                        "homeassistant",
                        "turn_off",
                        {
                            "entity_id": [
                                f"button.{DOMAIN}_mark_{subject_short}ed_{self.device}",
                                f"date.{DOMAIN}_last_{subject_short}ed_{self.device}",
                                f"number.{DOMAIN}_days_between_{subject}s_{self.device}",
                                f"binary_sensor.{DOMAIN}_{subject}_problem_{self.device}",
                                f"binary_sensor.{DOMAIN}_{subject}_todo_{self.device}",
                                f"sensor.{DOMAIN}_next_{subject}_{self.device}",
                            ]
                        },
                        blocking=True,
                    )

        await super().async_added_to_hass()

        def warning(msg: str) -> None:
            LOGGER.warning("%s :%s", self.unique_id, msg)

        # Load stored data
        if self.coordinator.data is None:
            warning("Coordinator not ready at initialization")
            return
        data = self.coordinator.data.get(self.unique_id)
        if data is None:
            if self._fallback_value is None:
                warning("Initialization failed as _fallback_value is None")
                return
            await self.async_select_option(self._fallback_value)
            return
        await self.async_select_option(data)

        # await _select_updated({"data": {"new_state": data}}, new_value=data)

        # Volg de select-waarde
        # self.async_on_remove(
        #     async_track_state_change_event(
        #         self.hass,
        #         f"select.{DOMAIN}_{self.entity_description.key}_{self.device}",
        #         _select_updated
        #     )
        # )

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        self._attr_current_option = option
        # Color
        if option in COLOR_MAPPING:
            self._attr_extra_state_attributes = {
                "state_color": True,
                "color": COLOR_MAPPING[option],
            }
        else:
            self._attr_extra_state_attributes = {"state_color": False}
        # Save to persistent storage
        if self.unique_id is not None:
            await self.coordinator.async_store_value(self.unique_id, option)
