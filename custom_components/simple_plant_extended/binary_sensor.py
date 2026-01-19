"""Binary sensor platform for simple_plant_extended."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util.dt import as_local

from .const import DOMAIN

if TYPE_CHECKING:
    from datetime import datetime

    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, EventStateChangedData, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


class SimplePlantExtendedBinarySensor(BinarySensorEntity):
    """simple_plant_extended binary_sensor base class."""

    _attr_has_entity_name = True
    _fallback_value: bool = False

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__()
        self._hass = hass
        self.entity_description = description
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][entry.entry_id]

        self._attr_should_poll = True

        device = self.coordinator.device

        self._attr_native_value: bool | None = None

        self.entity_id = f"binary_sensor.{DOMAIN}_{description.key}_{device}"
        self._attr_unique_id = f"{DOMAIN}_{description.key}_{device}"

        # Set up device info
        self._attr_device_info = self.coordinator.device_info

    @property
    def is_on(self) -> bool:
        """Return true if the binary_sensor is on."""
        return (
            self._fallback_value
            if self._attr_native_value is None
            else self._attr_native_value
        )

    @property
    def device(self) -> str | None:
        """Return the device name."""
        return self.coordinator.device

    async def get_dates(self) -> dict[str, datetime] | None:
        """Get dates from relevants device entites states."""
        return await self.coordinator.get_dates()

    async def async_added_to_hass(self) -> None:
        """Run when entity about to be added to hass."""
        await super().async_added_to_hass()

        last_date = None
        daysbetween = None
        if self.entity_description.key == "todo":
            last_date = f"date.{DOMAIN}_last_watered_{self.device}"
            daysbetween = f"number.{DOMAIN}_days_between_waterings_{self.device}"
        if "fertilization" in self.entity_description.key:
            last_date = f"date.{DOMAIN}_last_fertilized_{self.device}"
            daysbetween = f"number.{DOMAIN}_days_between_fertilizations_{self.device}"
        if "misting" in self.entity_description.key:
            last_date = f"date.{DOMAIN}_last_misted_{self.device}"
            daysbetween = f"number.{DOMAIN}_days_between_mistings_{self.device}"
        if "cleaning" in self.entity_description.key:
            last_date = f"date.{DOMAIN}_last_cleaned_{self.device}"
            daysbetween = f"number.{DOMAIN}_days_between_cleanings_{self.device}"

        # Subscribe to state changes
        if last_date not in ["unknown", "", "None", None]:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    last_date,
                    self._update_state,
                )
            )
        if daysbetween not in ["unknown", "", "None", None]:
            self.async_on_remove(
                async_track_state_change_event(
                    self.hass,
                    daysbetween,
                    self._update_state,
                )
            )

        self.async_on_remove(
            async_track_time_change(
                self.hass,
                self._update_state,
                hour=0,
                minute=0,
                second=0,
            )
        )

        # Initial update
        await self._update_state()

    async def _update_state(
        self,
        _event: Event[EventStateChangedData] | datetime | None = None,
    ) -> None:
        """Update the binary sensor state based on other entities."""
        raise NotImplementedError


class SimplePlantExtendedTodo(SimplePlantExtendedBinarySensor):
    """simple_plant_extended binary_sensor for todo."""

    _fallback_value = False

    async def _update_state(self, _event: Event | None = None) -> None:
        """Update the binary sensor state based on other entities."""
        dates = await self.get_dates()

        if not dates:
            return

        next_date = None
        if self.entity_description.key == "todo":
            next_date = "next_watering"
        if "fertilization" in self.entity_description.key:
            next_date = "next_fertilization"
        if "mist" in self.entity_description.key:
            next_date = "next_misting"
        if "clean" in self.entity_description.key:
            next_date = "next_cleaning"

        self._attr_native_value = (
            as_local(dates["today"]).date() >= as_local(dates[next_date]).date()
        )
        self.async_write_ha_state()


class SimplePlantExtendedProblem(SimplePlantExtendedBinarySensor):
    """simple_plant_extended binary_sensor for problem."""

    _fallback_value = False
    # _attr_translation_key = "problem"

    async def _update_state(self, _event: Event | None = None) -> None:
        """Update the binary sensor state based on other entities."""
        dates = await self.get_dates()

        if not dates:
            return

        next_date = None
        if self.entity_description.key == "problem":
            next_date = "next_watering"
        if "fertilization" in self.entity_description.key:
            next_date = "next_fertilization"
        if "misting" in self.entity_description.key:
            next_date = "next_misting"
        if "cleaning" in self.entity_description.key:
            next_date = "next_cleaning"

        self._attr_native_value = (
            as_local(dates["today"]).date() > as_local(dates[next_date]).date()
        )
        self.async_write_ha_state()


ENTITIES = [
    {
        "class": SimplePlantExtendedTodo,
        "description": BinarySensorEntityDescription(
            key="todo",
            translation_key="todo",
            name="Simple Plant Extended Binary Sensor Todo",
            icon="mdi:water-check-outline",
        ),
    },
    {
        "class": SimplePlantExtendedTodo,
        "description": BinarySensorEntityDescription(
            key="fertilization_todo",
            translation_key="fertilization_todo",
            name="Simple Plant Extended Binary Sensor Fertilization Todo",
            icon="mdi:water-check-outline",
        ),
    },
    {
        "class": SimplePlantExtendedTodo,
        "description": BinarySensorEntityDescription(
            key="misting_todo",
            translation_key="misting_todo",
            name="Simple Plant Extended Binary Sensor Misting Todo",
            icon="mdi:water-check-outline",
        ),
    },
    {
        "class": SimplePlantExtendedTodo,
        "description": BinarySensorEntityDescription(
            key="cleaning_todo",
            translation_key="cleaning_todo",
            name="Simple Plant Extended Binary Sensor Cleaning Todo",
            icon="mdi:water-check-outline",
        ),
    },
    {
        "class": SimplePlantExtendedProblem,
        "description": BinarySensorEntityDescription(
            key="problem",
            translation_key="problem",
            name="Simple Plant Extended Watering Problem",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon="mdi:water-alert-outline",
        ),
    },
    {
        "class": SimplePlantExtendedProblem,
        "description": BinarySensorEntityDescription(
            key="fertilization_problem",
            translation_key="fertilization_problem",
            name="Simple Plant Extended Fertilization Problem",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon="mdi:chili-alert-outline",
        ),
    },
    {
        "class": SimplePlantExtendedProblem,
        "description": BinarySensorEntityDescription(
            key="misting_problem",
            translation_key="misting_problem",
            name="Simple Plant Extended Misting Problem",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon="mdi:fan-alert",
        ),
    },
    {
        "class": SimplePlantExtendedProblem,
        "description": BinarySensorEntityDescription(
            key="cleaning_problem",
            translation_key="cleaning_problem",
            name="Simple Plant Extended Cleaning Problem",
            device_class=BinarySensorDeviceClass.PROBLEM,
            icon="mdi:wiper-wash-alert",
        ),
    },
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary_sensor platform."""
    async_add_entities(
        entity["class"](hass, entry, entity["description"]) for entity in ENTITIES
    )
