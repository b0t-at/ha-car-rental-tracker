"""Sensor platform for Car Rental Tracker."""
from __future__ import annotations

from datetime import date, datetime, timedelta
import logging
from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfLength
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.helpers.restore_state import RestoreEntity

from .calculations import calculate_rental_stats, RentalStats
from .const import (
    CONF_END_DATE,
    CONF_INITIAL_ODOMETER,
    CONF_KM_ALLOWANCE_PER_MONTH,
    CONF_ODOMETER_ENTITY,
    CONF_OVERAGE_COST_PER_KM,
    CONF_START_DATE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Car Rental Tracker sensors from a config entry."""
    config = entry.data
    
    # Create the coordinator for shared data
    coordinator = CarRentalCoordinator(hass, config)
    await coordinator.async_update()
    
    # Create sensor entities
    entities = [
        CarRentalCurrentOdometerSensor(coordinator, entry),
        CarRentalTotalDrivenSensor(coordinator, entry),
        CarRentalKmAllowedSensor(coordinator, entry),
        CarRentalKmRemainingSensor(coordinator, entry),
        CarRentalKmProjectedSensor(coordinator, entry),
        CarRentalTimeProgressSensor(coordinator, entry),
        CarRentalKmProgressSensor(coordinator, entry),
        CarRentalMonthlyDrivenSensor(coordinator, entry),
        CarRentalMonthlyRemainingSensor(coordinator, entry),
        CarRentalDaysRemainingSensor(coordinator, entry),
        CarRentalProjectedOverageSensor(coordinator, entry),
        CarRentalProjectedCostSensor(coordinator, entry),
        CarRentalStatusSensor(coordinator, entry),
    ]
    
    async_add_entities(entities, True)


class CarRentalCoordinator:
    """Coordinator to manage car rental data and calculations."""

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialize the coordinator."""
        self.hass = hass
        self.config = config
        self.stats: RentalStats | None = None
        self.current_odometer: float | None = None
        self._listeners: list[Callable[[], None]] = []
        
        # Set up state change listener for odometer entity
        self._remove_listener = async_track_state_change_event(
            hass,
            [config[CONF_ODOMETER_ENTITY]],
            self._handle_odometer_change,
        )
        
        # Set up periodic update (every 5 minutes to recalculate time-based metrics)
        self._remove_interval = async_track_time_interval(
            hass,
            self._handle_interval_update,
            DEFAULT_SCAN_INTERVAL,
        )

    async def _handle_odometer_change(self, event: Any) -> None:
        """Handle odometer entity state change."""
        new_state = event.data.get("new_state")
        if new_state is None:
            return
        
        try:
            self.current_odometer = float(new_state.state)
            await self.async_update()
            self._notify_listeners()
        except (ValueError, TypeError):
            _LOGGER.warning(
                "Invalid odometer value: %s", new_state.state
            )

    async def _handle_interval_update(self, now: datetime) -> None:
        """Handle periodic update."""
        await self.async_update()
        self._notify_listeners()

    async def async_update(self) -> None:
        """Update the coordinator data."""
        # Get current odometer reading
        if self.current_odometer is None:
            odometer_state = self.hass.states.get(self.config[CONF_ODOMETER_ENTITY])
            if odometer_state:
                try:
                    self.current_odometer = float(odometer_state.state)
                except (ValueError, TypeError):
                    _LOGGER.error(
                        "Cannot read odometer value from %s",
                        self.config[CONF_ODOMETER_ENTITY],
                    )
                    return
            else:
                _LOGGER.warning(
                    "Odometer entity %s not found",
                    self.config[CONF_ODOMETER_ENTITY],
                )
                return
        
        # Parse dates
        start_date = datetime.fromisoformat(self.config[CONF_START_DATE]).date()
        end_date = datetime.fromisoformat(self.config[CONF_END_DATE]).date()
        
        # Calculate statistics
        self.stats = calculate_rental_stats(
            start_date=start_date,
            end_date=end_date,
            km_allowance_per_month=self.config[CONF_KM_ALLOWANCE_PER_MONTH],
            initial_odometer=self.config[CONF_INITIAL_ODOMETER],
            current_odometer=self.current_odometer,
            overage_cost_per_km=self.config[CONF_OVERAGE_COST_PER_KM],
        )

    def add_listener(self, listener: Callable[[], None]) -> None:
        """Add a listener for data updates."""
        self._listeners.append(listener)

    def _notify_listeners(self) -> None:
        """Notify all listeners of data update."""
        for listener in self._listeners:
            listener()

    def remove(self) -> None:
        """Remove coordinator listeners."""
        if self._remove_listener:
            self._remove_listener()
        if self._remove_interval:
            self._remove_interval()


class CarRentalSensorBase(SensorEntity):
    """Base class for Car Rental Tracker sensors."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entry = entry
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Car Rental Tracker ({entry.data[CONF_START_DATE]})",
            manufacturer="Car Rental Tracker",
            model="KM Tracker",
            sw_version="1.0.0",
        )

    async def async_added_to_hass(self) -> None:
        """Handle entity added to hass."""
        await super().async_added_to_hass()
        self.coordinator.add_listener(self._handle_coordinator_update)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()


class CarRentalCurrentOdometerSensor(CarRentalSensorBase):
    """Sensor for current odometer reading."""

    _attr_name = "Current Odometer"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:counter"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_current_odometer"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        return self.coordinator.current_odometer


class CarRentalTotalDrivenSensor(CarRentalSensorBase):
    """Sensor for total KM driven."""

    _attr_name = "Total Driven"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:map-marker-distance"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_total_driven"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.total_driven_km
        return None


class CarRentalKmAllowedSensor(CarRentalSensorBase):
    """Sensor for total KM allowed."""

    _attr_name = "KM Allowed"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.TOTAL
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_km_allowed"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.km_allowed
        return None


class CarRentalKmRemainingSensor(CarRentalSensorBase):
    """Sensor for remaining KM."""

    _attr_name = "KM Remaining"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:gauge"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_km_remaining"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.km_remaining
        return None


class CarRentalKmProjectedSensor(CarRentalSensorBase):
    """Sensor for projected KM at contract end."""

    _attr_name = "KM Projected"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:chart-line"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_km_projected"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.km_projected
        return None


class CarRentalTimeProgressSensor(CarRentalSensorBase):
    """Sensor for time progress percentage."""

    _attr_name = "Time Progress"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:clock-outline"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_time_progress"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.time_progress
        return None


class CarRentalKmProgressSensor(CarRentalSensorBase):
    """Sensor for KM usage progress percentage."""

    _attr_name = "KM Progress"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:percent"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_km_progress"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.km_progress
        return None


class CarRentalMonthlyDrivenSensor(CarRentalSensorBase):
    """Sensor for KM driven this month."""

    _attr_name = "Monthly Driven"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-month"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_monthly_driven"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.monthly_driven_km
        return None


class CarRentalMonthlyRemainingSensor(CarRentalSensorBase):
    """Sensor for remaining KM this month."""

    _attr_name = "Monthly Remaining"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-check"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_monthly_remaining"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.monthly_remaining_km
        return None


class CarRentalDaysRemainingSensor(CarRentalSensorBase):
    """Sensor for days remaining in contract."""

    _attr_name = "Days Remaining"
    _attr_native_unit_of_measurement = "days"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:calendar-clock"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_days_remaining"

    @property
    def native_value(self) -> int | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.days_remaining
        return None


class CarRentalProjectedOverageSensor(CarRentalSensorBase):
    """Sensor for projected overage KM."""

    _attr_name = "Projected Overage"
    _attr_native_unit_of_measurement = UnitOfLength.KILOMETERS
    _attr_device_class = SensorDeviceClass.DISTANCE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:alert-circle"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_projected_overage"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.projected_overage_km
        return None


class CarRentalProjectedCostSensor(CarRentalSensorBase):
    """Sensor for projected overage cost."""

    _attr_name = "Projected Cost"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:currency-usd"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_projected_cost"

    @property
    def native_value(self) -> float | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.projected_cost
        return None


class CarRentalStatusSensor(CarRentalSensorBase):
    """Sensor for overall rental status."""

    _attr_name = "Status"
    _attr_icon = "mdi:information"

    def __init__(self, coordinator: CarRentalCoordinator, entry: ConfigEntry) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_status"

    @property
    def native_value(self) -> str | None:
        """Return the state of the sensor."""
        if self.coordinator.stats:
            return self.coordinator.stats.status
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        if not self.coordinator.stats:
            return {}
        
        return {
            "is_over_limit": self.coordinator.stats.is_over_limit,
            "is_projected_over": self.coordinator.stats.is_projected_over,
            "days_elapsed": self.coordinator.stats.days_elapsed,
            "days_total": self.coordinator.stats.days_total,
        }
