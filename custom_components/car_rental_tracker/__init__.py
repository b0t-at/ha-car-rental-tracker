"""Car Rental Tracker integration for Home Assistant.

This integration tracks car rental contracts with KM limits and provides
detailed statistics, projections, and visual dashboard capabilities.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import date, datetime
from functools import partial
import logging
from pathlib import Path
from typing import Any

from homeassistant.components.frontend import add_extra_js_url, remove_extra_js_url
from homeassistant.components.http import StaticPathConfig
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_UNIT_OF_MEASUREMENT, Platform, UnitOfLength
from homeassistant.core import (
    Event,
    EventStateChangedData,
    HomeAssistant,
    State,
    callback,
)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.helpers.storage import Store
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.loader import async_get_integration
from homeassistant.util import dt as dt_util

from .baseline import (
    MAX_DELAY_AFTER_BOUNDARY,
    SOURCE_FALLBACK,
    SOURCE_INITIAL,
    MonthBaseline,
    StateSnapshot,
    baseline_from_dict,
    baseline_month,
    baseline_to_dict,
    is_fallback_final,
    parse_odometer,
    select_month_start_baseline,
)
from .calculations import RentalStats, calculate_rental_stats
from .const import (
    BASELINE_RETRY_INTERVAL,
    CARD_FILENAME,
    CARD_URL_PATHS,
    CONF_END_DATE,
    CONF_INITIAL_ODOMETER,
    CONF_KM_ALLOWANCE_PER_MONTH,
    CONF_ODOMETER_ENTITY,
    CONF_OVERAGE_COST_PER_KM,
    CONF_START_DATE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    STORAGE_VERSION,
)

_LOGGER = logging.getLogger(__name__)

# List of platforms supported by this integration
PLATFORMS: list[Platform] = [Platform.SENSOR]

# Configuration schema (for configuration.yaml support)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)

# hass.data keys for the frontend card registration
DATA_CARD_URL = f"{DOMAIN}_card_url"
DATA_CARD_LOADED = f"{DOMAIN}_card_loaded"


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Car Rental Tracker component.

    Serves the Lovelace card and loads it in the frontend automatically.
    This runs once per Home Assistant start, so the static paths are only
    registered once.
    """
    www_path = str(Path(__file__).parent / "www")
    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(url_path=url_path, path=www_path, cache_headers=False)
            for url_path in CARD_URL_PATHS
        ]
    )

    integration = await async_get_integration(hass, DOMAIN)
    hass.data[DATA_CARD_URL] = (
        f"{CARD_URL_PATHS[0]}/{CARD_FILENAME}?v={integration.version}"
    )
    _load_card(hass)
    return True


@callback
def _load_card(hass: HomeAssistant) -> None:
    """Load the card in the frontend, unless it is already loaded."""
    if hass.data.get(DATA_CARD_LOADED):
        return
    card_url = hass.data[DATA_CARD_URL]
    add_extra_js_url(hass, card_url)
    hass.data[DATA_CARD_LOADED] = True
    _LOGGER.debug("Registered Car Rental Tracker card at %s", card_url)


@callback
def _unload_card(hass: HomeAssistant) -> None:
    """Stop loading the card in the frontend."""
    if not hass.data.get(DATA_CARD_LOADED):
        return
    remove_extra_js_url(hass, hass.data[DATA_CARD_URL])
    hass.data[DATA_CARD_LOADED] = False
    _LOGGER.debug("Removed Car Rental Tracker card from the frontend")


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Car Rental Tracker from a config entry."""
    # The card may have been removed together with the last entry; async_setup
    # only runs once per Home Assistant start, so load it again here.
    _load_card(hass)

    coordinator = CarRentalCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_start_tracking()
    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Reload when the configuration is changed through the options flow
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    return True


async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry after its configuration was changed."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry.

    The coordinator and its listeners are torn down through the callbacks
    registered with entry.async_on_unload.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Clean up when an entry is deleted.

    Removes the persisted month-start baseline, and stops loading the card in
    the frontend once the last entry is gone.
    """
    await _baseline_store(hass, entry).async_remove()

    # The entry being removed is still listed while this runs.
    remaining = [
        other
        for other in hass.config_entries.async_entries(DOMAIN)
        if other.entry_id != entry.entry_id
    ]
    if not remaining:
        _unload_card(hass)


def _baseline_store(hass: HomeAssistant, entry: ConfigEntry) -> Store[dict[str, Any]]:
    """Return the store holding the month-start baseline of an entry."""
    return Store(hass, STORAGE_VERSION, f"{DOMAIN}.{entry.entry_id}")


@dataclass(frozen=True)
class CarRentalData:
    """Data provided by the coordinator."""

    stats: RentalStats
    current_odometer: float
    monthly_baseline: float | None
    monthly_baseline_source: str


class CarRentalCoordinator(DataUpdateCoordinator[CarRentalData | None]):
    """Coordinator that reads the odometer and calculates the statistics.

    The data is None until the odometer has reported a valid reading.
    """

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        config = entry.data
        self._entity_id: str = config[CONF_ODOMETER_ENTITY]
        self._start_date = datetime.fromisoformat(config[CONF_START_DATE]).date()
        self._end_date = datetime.fromisoformat(config[CONF_END_DATE]).date()
        self._store = _baseline_store(hass, entry)
        self._lock = asyncio.Lock()

        # Last two valid odometer readings, kept to capture the value at the
        # month boundary without needing the recorder.
        self._last_snapshot: StateSnapshot | None = None
        self._previous_snapshot: StateSnapshot | None = None

        self._baseline: MonthBaseline | None = None
        self._baseline_retry_after: datetime | None = None
        self._baseline_final = False
        self._history_error_logged = False
        self._unit_warning_logged = False
        self._missing_logged = False

    async def _async_setup(self) -> None:
        """Load the persisted month-start baseline."""
        self._baseline = baseline_from_dict(
            await self._store.async_load(), self._entity_id
        )

    @callback
    def async_start_tracking(self) -> None:
        """Refresh on odometer changes until the entry is unloaded."""
        self.config_entry.async_on_unload(
            async_track_state_change_event(
                self.hass, [self._entity_id], self._async_handle_odometer_event
            )
        )

    @callback
    def _async_handle_odometer_event(
        self, event: Event[EventStateChangedData]
    ) -> None:
        """Handle a state change of the odometer entity."""
        new_state = event.data["new_state"]
        old_state = event.data["old_state"]
        if new_state is None or parse_odometer(new_state.state) is None:
            _LOGGER.debug(
                "Ignoring non-numeric odometer state of %s: %s",
                self._entity_id,
                new_state.state if new_state else None,
            )
            return
        if old_state is not None and old_state.state == new_state.state:
            return

        self._record_state(new_state)
        self.config_entry.async_create_task(
            self.hass, self.async_request_refresh(), "car_rental_tracker_refresh"
        )

    def _record_state(self, state: State) -> None:
        """Remember a valid odometer reading and when its value was set."""
        snapshot = StateSnapshot(state.state, state.last_changed)
        if self._last_snapshot != snapshot:
            self._previous_snapshot = self._last_snapshot
            self._last_snapshot = snapshot
        self._check_unit(state)

    def _check_unit(self, state: State) -> None:
        """Warn once when the source odometer does not report kilometers."""
        unit = state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
        if unit in (None, "", UnitOfLength.KILOMETERS) or self._unit_warning_logged:
            return
        self._unit_warning_logged = True
        _LOGGER.warning(
            "Odometer entity %s reports '%s' instead of km; values are used "
            "unconverted and treated as km",
            self._entity_id,
            unit,
        )

    def _read_odometer(self) -> float | None:
        """Read the current odometer value, or the last valid one."""
        state = self.hass.states.get(self._entity_id)
        if state is not None and parse_odometer(state.state) is not None:
            self._record_state(state)
            self._missing_logged = False
        elif not self._missing_logged:
            self._missing_logged = True
            _LOGGER.debug(
                "Odometer entity %s has no valid reading (state: %s)",
                self._entity_id,
                state.state if state else "missing",
            )

        if self._last_snapshot is None:
            return None
        return parse_odometer(self._last_snapshot.state)

    async def _async_update_data(self) -> CarRentalData | None:
        """Calculate the rental statistics."""
        async with self._lock:
            current_odometer = self._read_odometer()
            if current_odometer is None:
                return None

            today = dt_util.now().date()
            month = baseline_month(today, self._start_date, self._end_date)
            if month is None:
                baseline = MonthBaseline(today.replace(day=1), None, SOURCE_INITIAL)
            else:
                baseline = await self._async_get_baseline(month)

            config = self.config_entry.data
            stats = calculate_rental_stats(
                start_date=self._start_date,
                end_date=self._end_date,
                km_allowance_per_month=config[CONF_KM_ALLOWANCE_PER_MONTH],
                initial_odometer=config[CONF_INITIAL_ODOMETER],
                current_odometer=current_odometer,
                overage_cost_per_km=config[CONF_OVERAGE_COST_PER_KM],
                odometer_at_month_start=baseline.value,
                today=today,
            )
            return CarRentalData(
                stats=stats,
                current_odometer=current_odometer,
                monthly_baseline=baseline.value,
                monthly_baseline_source=baseline.source,
            )

    async def _async_get_baseline(self, month: date) -> MonthBaseline:
        """Return the odometer baseline for the month, computed once per month.

        A baseline found in history is cached and persisted for the month.
        The estimate fallback is retried at most once per retry interval, and
        no longer once a retry cannot find a baseline anymore.
        """
        cached = self._baseline
        now = dt_util.utcnow()
        if cached is not None and cached.month == month:
            if cached.source != SOURCE_FALLBACK or self._baseline_final:
                return cached
            if self._baseline_retry_after and now < self._baseline_retry_after:
                return cached

        boundary = dt_util.as_utc(dt_util.start_of_local_day(month))
        history, history_available = await self._async_get_history(boundary)
        candidates: list[Any] = [self._previous_snapshot, self._last_snapshot]
        candidates.extend(history)
        value, source = select_month_start_baseline(candidates, boundary)
        baseline = MonthBaseline(month, value, source)
        self._baseline = baseline
        self._baseline_final = False

        if source == SOURCE_FALLBACK:
            self._baseline_final = is_fallback_final(
                history_available, now, boundary
            )
            self._baseline_retry_after = now + BASELINE_RETRY_INTERVAL
            _LOGGER.debug(
                "No odometer reading near %s for %s, estimating monthly stats",
                boundary,
                self._entity_id,
            )
        else:
            self._baseline_retry_after = None
            await self._store.async_save(baseline_to_dict(self._entity_id, baseline))
        return baseline

    async def _async_get_history(
        self, boundary: datetime
    ) -> tuple[list[State], bool]:
        """Return recorded odometer states around the month boundary.

        The flag is False when the recorder could not be read, so a retry may
        still find states.
        """
        if "recorder" not in self.hass.config.components:
            return [], True

        # pylint: disable-next=import-outside-toplevel
        from homeassistant.components.recorder import get_instance

        # pylint: disable-next=import-outside-toplevel
        from homeassistant.components.recorder.history import (
            state_changes_during_period,
        )

        try:
            states = await get_instance(self.hass).async_add_executor_job(
                partial(
                    state_changes_during_period,
                    self.hass,
                    boundary,
                    boundary + MAX_DELAY_AFTER_BOUNDARY,
                    self._entity_id,
                    no_attributes=True,
                    include_start_time_state=True,
                )
            )
        except Exception:  # noqa: BLE001 - never let the recorder break updates
            if not self._history_error_logged:
                self._history_error_logged = True
                _LOGGER.warning(
                    "Could not read odometer history of %s from the recorder",
                    self._entity_id,
                    exc_info=True,
                )
            return [], False

        self._history_error_logged = False
        return list(states.get(self._entity_id, [])), True
