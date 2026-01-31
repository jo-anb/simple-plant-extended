"""Button platform for simple_plant_extended."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.button import (
    ButtonEntity,
    ButtonEntityDescription,
)

from .const import DOMAIN

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


ENTITY_DESCRIPTIONS = (
    ButtonEntityDescription(
        key="mark_watered",
        translation_key="mark_watered",
        icon="mdi:watering-can",
    ),
    ButtonEntityDescription(
        key="mark_fertilized",
        translation_key="mark_fertilized",
        icon="mdi:seed-outline",
    ),
    ButtonEntityDescription(
        key="mark_misted",
        translation_key="mark_misted",
        icon="mdi:spray-bottle",
    ),
    ButtonEntityDescription(
        key="mark_cleaned",
        translation_key="mark_cleaned",
        icon="mdi:shimmer",
    ),
    ButtonEntityDescription(
        key="update_data",
        translation_key="update_data",
        icon="mdi:sync",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the button platform."""
    async_add_entities(
        SimplePlantExtendedButton(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantExtendedButton(ButtonEntity):
    """simple_plant_extended button class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: ButtonEntityDescription,
    ) -> None:
        """Initialize the button class."""
        super().__init__()

        self.entity_description = description
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        device = self.coordinator.device

        self.entity_id = f"button.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        # Set up device info
        self._attr_device_info = self.coordinator.device_info

    @property
    def device(self) -> str | None:
        """Return the device name."""
        return self.coordinator.device

    @property
    def extra_state_attributes(self) -> dict:
        """Return device attributes."""
        return dict(self.coordinator.device_attributes)

    async def get_dates(self) -> dict[str, datetime] | None:
        """Get dates from relevants device entites states."""
        return await self.coordinator.get_dates()

    async def async_press(self) -> None:
        """Press the button."""
        actions = [self.entity_description.key.split("_")[1]]
        if actions[0] == "fertilized":
            actions = ["fertilized", "watered"]

        if self.entity_description.key != "update_data":
            for action in actions:
                await self.coordinator.async_mark_action_toggle(action=action)

        if self.entity_description.key == "update_data":
            await self.coordinator.async_migrate_data()
