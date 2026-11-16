"""Constants for the Car Rental Tracker integration."""
from __future__ import annotations

from datetime import timedelta
from typing import Final

# Integration domain
DOMAIN: Final = "car_rental_tracker"

# Frontend card
CARD_FILENAME: Final = "car-rental-card.js"
# The card is loaded from CARD_URL, which no other component serves. The legacy
# paths stay available for Lovelace resources added by hand in older versions.
CARD_URL: Final = f"/{DOMAIN}/{CARD_FILENAME}"
CARD_LEGACY_URL_PATHS: Final = (f"/hacsfiles/{DOMAIN}", f"/local/community/{DOMAIN}")

# Configuration keys
CONF_NAME: Final = "name"
CONF_START_DATE: Final = "start_date"
CONF_END_DATE: Final = "end_date"
CONF_KM_ALLOWANCE_PER_MONTH: Final = "km_allowance_per_month"
CONF_INITIAL_ODOMETER: Final = "initial_odometer"
CONF_OVERAGE_COST_PER_KM: Final = "overage_cost_per_km"
CONF_ODOMETER_ENTITY: Final = "odometer_entity"

# Default values
DEFAULT_NAME: Final = "Car Rental Tracker"
DEFAULT_KM_ALLOWANCE: Final = 1000
DEFAULT_OVERAGE_COST: Final = 0.25
DEFAULT_SCAN_INTERVAL: Final = timedelta(minutes=5)

# Month-start baseline: retry interval while only the estimate is available
BASELINE_RETRY_INTERVAL: Final = timedelta(hours=1)
STORAGE_VERSION: Final = 1

# A lower odometer reading than the last one is ignored when it drops by more
# than this many km (sensor glitch). Smaller drops are rounding jitter.
ODOMETER_ROLLBACK_TOLERANCE: Final = 1.0
# Lower readings are accepted once the source has reported them this long, so
# a changed source or a single too-high glitch doesn't block the odometer.
ODOMETER_ROLLBACK_ACCEPT_AFTER: Final = timedelta(hours=1)

# Odometer domain whose values are entered by hand; a lower value there is a
# deliberate correction and is always accepted.
MANUAL_ODOMETER_DOMAIN: Final = "input_number"

# Sensor keys (unique_id suffix and translation key)
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
SENSOR_DAYS_ELAPSED: Final = "days_elapsed"
SENSOR_PROJECTED_OVERAGE: Final = "projected_overage"
SENSOR_PROJECTED_COST: Final = "projected_cost"
SENSOR_STATUS: Final = "status"
SENSOR_TARGET_TODAY: Final = "target_today"
SENSOR_DEVIATION_TODAY: Final = "deviation_today"
SENSOR_DAILY_AVERAGE: Final = "daily_average"
SENSOR_DAILY_TARGET: Final = "daily_target"
