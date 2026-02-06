"""Text platform for simple_plant_extended."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.text import (
    TextEntity,
    TextEntityDescription,
    TextMode,
)

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


ENTITY_DESCRIPTIONS = (
    TextEntityDescription(
        key="notes",
        translation_key="notes",
        icon="mdi:note-text",
    ),
    TextEntityDescription(
        key="species",
        translation_key="species",
        icon="mdi:leaf",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the text platform."""
    async_add_entities(
        SimplePlantExtendedText(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantExtendedText(TextEntity):
    """simple_plant_extended text class."""

    _attr_has_entity_name = True
    _attr_mode = TextMode.TEXT
    _attr_native_min_value = 0
    _attr_native_max_value = 2048

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: TextEntityDescription,
    ) -> None:
        """Initialize the text class."""
        super().__init__()
        self._hass = hass
        self._entry = entry
        self.entity_description = description
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        device = self.coordinator.device

        self.entity_id = f"text.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        self._fallback_value = str(entry.data.get(description.key, ""))

        # Set up device info
        self._attr_device_info = self.coordinator.device_info

    @property
    def device(self) -> str | None:
        """Return the device name."""
        return self.coordinator.device

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        def warning(msg: str) -> None:
            LOGGER.warning("%s :%s", self.unique_id, msg)

        if self.coordinator.data is None:
            warning("Coordinator not ready at initialization")
            return

        data = self.coordinator.data.get(self.unique_id)
        if data is None:
            await self.async_set_value(self._fallback_value)
            return

        await self.async_set_value(str(data))

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        self._attr_native_value = value
        self.async_write_ha_state()

        if self.unique_id is not None:
            await self.coordinator.async_store_value(self.unique_id, value)

        if self._entry.data.get(self.entity_description.key) != value:
            data = dict(self._entry.data)
            data[self.entity_description.key] = value
            self._hass.config_entries.async_update_entry(self._entry, data=data)
