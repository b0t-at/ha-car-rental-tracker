"""Constants for the Car Rental Tracker integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "car_rental_tracker"

# Configuration keys
CONF_START_DATE: Final = "start_date"
CONF_END_DATE: Final = "end_date"
CONF_KM_ALLOWANCE_PER_MONTH: Final = "km_allowance_per_month"
CONF_INITIAL_ODOMETER: Final = "initial_odometer"
CONF_OVERAGE_COST_PER_KM: Final = "overage_cost_per_km"
CONF_ODOMETER_ENTITY: Final = "odometer_entity"

# Default values
DEFAULT_KM_ALLOWANCE: Final = 1000
DEFAULT_OVERAGE_COST: Final = 0.25
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)

# Sensor unique IDs
SENSOR_CURRENT_ODOMETER: Final = "current_odometer"
SENSOR_TOTAL_DRIVEN: Final = "total_driven"
SENSOR_KM_ALLOWED: Final = "km_allowed"
SENSOR_KM_REMAINING: Final = "km_remaining"
SENSOR_KM_PROJECTED: Final = "km_projected"
SENSOR_TIME_PROGRESS: Final = "time_progress"
SENSOR_KM_PROGRESS: Final = "km_progress"
SENSOR_MONTHLY_DRIVEN: Final = "monthly_driven"
SENSOR_MONTHLY_REMAINING: Final = "monthly_remaining"
SENSOR_MONTHLY_ALLOWANCE: Final = "monthly_allowance"
SENSOR_DAYS_REMAINING: Final = "days_remaining"
SENSOR_PROJECTED_OVERAGE: Final = "projected_overage"
SENSOR_PROJECTED_COST: Final = "projected_cost"
SENSOR_STATUS: Final = "status"

# Status values
STATUS_OK: Final = "ok"
STATUS_WARNING: Final = "warning"
STATUS_CRITICAL: Final = "critical"

# Thresholds
WARNING_THRESHOLD: Final = 0.85  # 85% usage triggers warning
CRITICAL_THRESHOLD: Final = 1.0  # 100% usage triggers critical
