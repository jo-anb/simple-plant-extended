"""Sensor platform for simple_plant_extended."""

from __future__ import annotations

from datetime import date, datetime
from typing import TYPE_CHECKING

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_change,
)
from homeassistant.util.dt import as_local, utcnow

from .const import DOMAIN

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.core import Event, EventStateChangedData, HomeAssistant
    from homeassistant.helpers.entity_platform import AddEntitiesCallback

    from .coordinator import SimplePlantExtendedCoordinator


ENTITY_DESCRIPTIONS = (
    SensorEntityDescription(
        device_class=SensorDeviceClass.DATE,
        key="next_watering",
        translation_key="next_watering",
        icon="mdi:clipboard-text-clock",
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.DATE,
        key="next_fertilization",
        translation_key="next_fertilization",
        icon="mdi:clipboard-text-clock",
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.DATE,
        key="next_misting",
        translation_key="next_misting",
        icon="mdi:clipboard-text-clock",
    ),
    SensorEntityDescription(
        device_class=SensorDeviceClass.DATE,
        key="next_cleaning",
        translation_key="next_cleaning",
        icon="mdi:clipboard-text-clock",
    ),
    SensorEntityDescription(
        key="current_humidity",
        translation_key="current_humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement="%",
        icon="mdi:water-percent",
    ),
    SensorEntityDescription(
        key="current_temperature",
        translation_key="current_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        icon="mdi:thermometer",
    ),
    SensorEntityDescription(
        key="current_light",
        translation_key="current_light",
        device_class=SensorDeviceClass.ILLUMINANCE,
        icon="mdi:brightness-6",
    ),
    SensorEntityDescription(
        key="plant_age_days",
        translation_key="plant_age_days",
        native_unit_of_measurement="days",
        icon="mdi:calendar-clock",
    ),
)

COLOR_MAPPING = {"Today": "Goldenrod", "Late": "Tomato"}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    async_add_entities(
        SimplePlantExtendedSensor(hass, entry, entity_description)
        for entity_description in ENTITY_DESCRIPTIONS
    )


class SimplePlantExtendedSensor(SensorEntity):
    """simple_plant_extended sensor class."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor class."""
        super().__init__()
        self.entity_description = description
        self._fallback_value: date | None = None
        self._attr_native_value: date | None = None
        self.coordinator: SimplePlantExtendedCoordinator = hass.data[DOMAIN][
            entry.entry_id
        ]

        device = self.coordinator.device

        self.entity_id = f"sensor.{DOMAIN}_{description.key}_{device}"
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

    @property
    def extra_state_attributes(self) -> dict:
        """Return device attributes merged with state attributes."""
        attrs: dict = {}
        if self._attr_extra_state_attributes:
            attrs.update(self._attr_extra_state_attributes)
        attrs.update(self.coordinator.device_attributes)
        return attrs

    @property
    def native_value(self) -> date | None:
        """Return true if the binary_sensor is on."""
        return (
            self._fallback_value
            if self._attr_native_value is None
            else self._attr_native_value
        )

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to hass."""
        await super().async_added_to_hass()

        # Handle linked sensor entities (humidity, temperature, light)
        if self.entity_description.key in ["current_humidity", "current_temperature", "current_light"]:
            sensor_key_map = {
                "current_humidity": "humidity_sensor",
                "current_temperature": "temperature_sensor",
                "current_light": "light_sensor",
            }
            sensor_entity_id = self.entry.data.get(sensor_key_map[self.entity_description.key])

            if sensor_entity_id:
                self.async_on_remove(
                    async_track_state_change_event(
                        self.hass,
                        sensor_entity_id,
                        self._update_linked_sensor,
                    )
                )
            # Initial update
            await self._update_linked_sensor()
            return

        # Handle plant age sensor
        if self.entity_description.key == "plant_age_days":
            self.async_on_remove(
                async_track_time_change(
                    self.hass,
                    self._update_plant_age,
                    hour=0,
                    minute=0,
                    second=0,
                )
            )
            # Initial update
            await self._update_plant_age()
            return

        # Existing date sensors logic
        last_date = None
        daysbetween = None
        if "watering" in self.entity_description.key:
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

        self.async_on_remove(
            async_track_state_change_event(
                self.hass,
                last_date,
                self._update_state,
            )
        )
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
        self, _event: Event[EventStateChangedData] | datetime | None = None
    ) -> None:
        """Update the binary sensor state based on other entities."""
        dates = await self.coordinator.get_dates()

        if not dates:
            return

        key = None
        if "water" in self.entity_description.key:
            key = "next_watering"
        if "fertilization" in self.entity_description.key:
            key = "next_fertilization"
        if "misting" in self.entity_description.key:
            key = "next_misting"
        if "cleaning" in self.entity_description.key:
            key = "next_cleaning"

        # Color
        today = as_local(dates["today"]).date()
        next_action_date = as_local(datetime.fromisoformat("1970-01-01")).date()
        if as_local(dates[key]).date() not in ["unknown", "", None]:
            next_action_date = as_local(dates[key]).date()

        color_key = "OK"
        if today == next_action_date:
            color_key = "Today"
        if today > next_action_date:
            color_key = "Late"

        if color_key in COLOR_MAPPING:
            self._attr_extra_state_attributes = {
                "state_color": True,
                "color": COLOR_MAPPING[color_key],
            }
        else:
            self._attr_extra_state_attributes = {"state_color": False}

        # Value
        self._attr_native_value = next_action_date
        self.async_write_ha_state()

    async def _update_linked_sensor(
        self, _event: Event[EventStateChangedData] | None = None
    ) -> None:
        """Update sensor value from linked external sensor."""
        sensor_key_map = {
            "current_humidity": "humidity_sensor",
            "current_temperature": "temperature_sensor",
            "current_light": "light_sensor",
        }

        sensor_entity_id = self.entry.data.get(sensor_key_map[self.entity_description.key])

        if not sensor_entity_id:
            self._attr_native_value = None
            self._attr_available = False
            self.async_write_ha_state()
            return

        state = self.hass.states.get(sensor_entity_id)
        if state and state.state not in ["unknown", "unavailable", None]:
            try:
                self._attr_native_value = float(state.state)
                self._attr_available = True
            except (ValueError, TypeError):
                self._attr_native_value = None
                self._attr_available = False
        else:
            self._attr_native_value = None
            self._attr_available = False

        self.async_write_ha_state()

    async def _update_plant_age(
        self, _event: datetime | None = None
    ) -> None:
        """Update plant age in days."""
        acquisition_date = self.entry.data.get("acquisition_date")

        if not acquisition_date:
            self._attr_native_value = None
            self._attr_available = False
            self.async_write_ha_state()
            return

        try:
            acq_date = date.fromisoformat(acquisition_date)
            today = utcnow().date()
            age_days = (today - acq_date).days
            self._attr_native_value = age_days
            self._attr_available = True
        except (ValueError, TypeError):
            self._attr_native_value = None
            self._attr_available = False

        self.async_write_ha_state()
