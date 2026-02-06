"""Number platform for simple_plant_extended."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfLength, UnitOfTime

from .const import DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


ENTITY_DESCRIPTIONS = (
    NumberEntityDescription(
        key="days_between_waterings",
        translation_key="days_between_waterings",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.BOX,
        icon="mdi:counter",
        native_step=0,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    NumberEntityDescription(
        key="days_between_fertilizations",
        translation_key="days_between_fertilizations",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.BOX,
        icon="mdi:counter",
        native_step=0,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    NumberEntityDescription(
        key="days_between_mistings",
        translation_key="days_between_mistings",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.BOX,
        icon="mdi:counter",
        native_step=0,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    NumberEntityDescription(
        key="days_between_cleanings",
        translation_key="days_between_cleanings",
        device_class=NumberDeviceClass.DURATION,
        mode=NumberMode.BOX,
        icon="mdi:counter",
        native_step=0,
        native_unit_of_measurement=UnitOfTime.DAYS,
    ),
    NumberEntityDescription(
        key="distance_to_window",
        translation_key="distance_to_window",
        device_class=NumberDeviceClass.DISTANCE,
        mode=NumberMode.BOX,
        icon="mdi:ruler",
        native_min_value=0,
        native_max_value=1000,
        native_step=10,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
    ),
    NumberEntityDescription(
        key="pot_diameter",
        translation_key="pot_diameter",
        device_class=NumberDeviceClass.DISTANCE,
        mode=NumberMode.BOX,
        icon="mdi:circle-double",
        native_min_value=5,
        native_max_value=200,
        native_step=1,
        native_unit_of_measurement=UnitOfLength.CENTIMETERS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the number platform."""
    async_add_entities(
        SimplePlantExtendedNumber(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantExtendedNumber(NumberEntity):
    """simple_plant_extended number class."""

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_native_min_value = 1
    _attr_native_max_value = 360
    _attr_native_step = 1

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: NumberEntityDescription,
    ) -> None:
        """Initialize the number class."""
        super().__init__()
        self._hass = hass
        self._entry = entry
        self.entity_description = description
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        device = self.coordinator.device

        self.entity_id = f"number.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        if description.native_min_value is not None:
            self._attr_native_min_value = description.native_min_value
        if description.native_max_value is not None:
            self._attr_native_max_value = description.native_max_value
        if description.native_step is not None:
            self._attr_native_step = description.native_step

        # set value
        self._fallback_value = entry.data.get(description.key)

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
            if self._fallback_value is None:
                warning("Initialization failed as _fallback_value is None")
                return
            await self.async_set_native_value(self._fallback_value)
            return
        await self.async_set_native_value(float(data))

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        self._attr_native_value = value
        self.async_write_ha_state()

        # Save to persistent storage
        if self.unique_id is not None:
            await self.coordinator.async_store_value(self.unique_id, str(value))
