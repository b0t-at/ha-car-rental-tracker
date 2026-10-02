"""Sensor platform for Car Rental Tracker."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

try:
    from homeassistant.const import UnitOfRatio

    PERCENTAGE: str = UnitOfRatio.PERCENTAGE
except ImportError:  # Home Assistant < 2026.7
    from homeassistant.const import PERCENTAGE

from . import CarRentalCoordinator, CarRentalData
from .calculations import STATUS_CRITICAL, STATUS_OK, STATUS_WARNING
from .const import (
    CONF_START_DATE,
    DOMAIN,
    SENSOR_CURRENT_ODOMETER,
    SENSOR_DAYS_ELAPSED,
    SENSOR_DAYS_REMAINING,
    SENSOR_KM_ALLOWED,
    SENSOR_KM_PROGRESS,
    SENSOR_KM_PROJECTED,
    SENSOR_KM_REMAINING,
    SENSOR_MONTHLY_ALLOWANCE,
    SENSOR_MONTHLY_DRIVEN,
    SENSOR_MONTHLY_REMAINING,
    SENSOR_PROJECTED_COST,
    SENSOR_PROJECTED_OVERAGE,
    SENSOR_STATUS,
    SENSOR_TIME_PROGRESS,
    SENSOR_TOTAL_DRIVEN,
)


@dataclass(frozen=True, kw_only=True)
class CarRentalSensorEntityDescription(SensorEntityDescription):
    """Describes a Car Rental Tracker sensor."""

    value_fn: Callable[[CarRentalData], StateType]
    attributes_fn: Callable[[CarRentalData], dict[str, Any]] | None = None


def _distance(
    key: str,
    icon: str,
    value_fn: Callable[[CarRentalData], StateType],
    state_class: SensorStateClass = SensorStateClass.MEASUREMENT,
    attributes_fn: Callable[[CarRentalData], dict[str, Any]] | None = None,
) -> CarRentalSensorEntityDescription:
    """Return the description of a sensor reporting kilometers."""
    return CarRentalSensorEntityDescription(
        key=key,
        translation_key=key,
        icon=icon,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=state_class,
        value_fn=value_fn,
        attributes_fn=attributes_fn,
    )


def _percentage(
    key: str, icon: str, value_fn: Callable[[CarRentalData], StateType]
) -> CarRentalSensorEntityDescription:
    """Return the description of a sensor reporting a percentage."""
    return CarRentalSensorEntityDescription(
        key=key,
        translation_key=key,
        icon=icon,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=value_fn,
    )


def _days(
    key: str, icon: str, value_fn: Callable[[CarRentalData], StateType]
) -> CarRentalSensorEntityDescription:
    """Return the description of a sensor reporting a number of days."""
    return CarRentalSensorEntityDescription(
        key=key,
        translation_key=key,
        icon=icon,
        native_unit_of_measurement=UnitOfTime.DAYS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=value_fn,
    )


SENSOR_DESCRIPTIONS: tuple[CarRentalSensorEntityDescription, ...] = (
    _distance(
        SENSOR_CURRENT_ODOMETER,
        "mdi:counter",
        lambda data: data.current_odometer,
        SensorStateClass.TOTAL_INCREASING,
    ),
    _distance(
        SENSOR_TOTAL_DRIVEN,
        "mdi:map-marker-distance",
        lambda data: data.stats.total_driven_km,
        SensorStateClass.TOTAL,
    ),
    _distance(SENSOR_KM_ALLOWED, "mdi:speedometer", lambda data: data.stats.km_allowed),
    _distance(SENSOR_KM_REMAINING, "mdi:gauge", lambda data: data.stats.km_remaining),
    _distance(
        SENSOR_KM_PROJECTED, "mdi:chart-line", lambda data: data.stats.km_projected
    ),
    _percentage(
        SENSOR_TIME_PROGRESS, "mdi:clock-outline", lambda data: data.stats.time_progress
    ),
    _percentage(SENSOR_KM_PROGRESS, "mdi:percent", lambda data: data.stats.km_progress),
    _distance(
        SENSOR_MONTHLY_DRIVEN,
        "mdi:calendar-month",
        lambda data: data.stats.monthly_driven_km,
        attributes_fn=lambda data: {
            "monthly_baseline_source": data.monthly_baseline_source,
            "monthly_baseline": data.monthly_baseline,
        },
    ),
    _distance(
        SENSOR_MONTHLY_REMAINING,
        "mdi:calendar-check",
        lambda data: data.stats.monthly_remaining_km,
    ),
    _distance(
        SENSOR_MONTHLY_ALLOWANCE,
        "mdi:calendar-range",
        lambda data: data.stats.monthly_allowance_km,
    ),
    _days(
        SENSOR_DAYS_REMAINING,
        "mdi:calendar-clock",
        lambda data: data.stats.days_remaining,
    ),
    _days(
        SENSOR_DAYS_ELAPSED, "mdi:calendar-check", lambda data: data.stats.days_elapsed
    ),
    _distance(
        SENSOR_PROJECTED_OVERAGE,
        "mdi:alert-circle",
        lambda data: data.stats.projected_overage_km,
    ),
    # The unit (Home Assistant's currency) is set on the entity at runtime.
    CarRentalSensorEntityDescription(
        key=SENSOR_PROJECTED_COST,
        translation_key=SENSOR_PROJECTED_COST,
        icon="mdi:cash",
        device_class=SensorDeviceClass.MONETARY,
        value_fn=lambda data: data.stats.projected_cost,
    ),
    CarRentalSensorEntityDescription(
        key=SENSOR_STATUS,
        translation_key=SENSOR_STATUS,
        icon="mdi:information",
        device_class=SensorDeviceClass.ENUM,
        options=[STATUS_OK, STATUS_WARNING, STATUS_CRITICAL],
        value_fn=lambda data: data.stats.status,
        attributes_fn=lambda data: {
            "is_over_limit": data.stats.is_over_limit,
            "is_projected_over": data.stats.is_projected_over,
            "days_elapsed": data.stats.days_elapsed,
            "days_total": data.stats.days_total,
        },
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Car Rental Tracker sensors from a config entry."""
    coordinator: CarRentalCoordinator = entry.runtime_data
    async_add_entities(
        CarRentalSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class CarRentalSensor(CoordinatorEntity[CarRentalCoordinator], SensorEntity):
    """Sensor exposing one value of the Car Rental Tracker statistics."""

    _attr_has_entity_name = True
    entity_description: CarRentalSensorEntityDescription

    def __init__(
        self,
        coordinator: CarRentalCoordinator,
        entry: ConfigEntry,
        description: CarRentalSensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        if description.device_class == SensorDeviceClass.MONETARY:
            self._attr_native_unit_of_measurement = coordinator.hass.config.currency
        # The device name determines the entity ids, e.g.
        # sensor.car_rental_tracker_2024_01_01_km_remaining
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Car Rental Tracker ({entry.data[CONF_START_DATE]})",
            manufacturer="Car Rental Tracker",
            model="KM Tracker",
            entry_type=DeviceEntryType.SERVICE,
        )

    @property
    def available(self) -> bool:
        """Return True once the odometer has reported a valid reading."""
        return super().available and self.coordinator.data is not None

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if self.coordinator.data is None or self.entity_description.attributes_fn is None:
            return None
        return self.entity_description.attributes_fn(self.coordinator.data)
