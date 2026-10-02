"""Month-start odometer baseline selection for Car Rental Tracker.

This module is intentionally free of Home Assistant imports so it can be
unit tested without Home Assistant installed. State-like inputs only need a
``state`` and a timezone-aware ``last_updated`` attribute, which both Home
Assistant ``State`` objects and :class:`StateSnapshot` provide.
"""
from __future__ import annotations

from collections.abc import Iterable
from datetime import date, datetime, timedelta
import math
from typing import Any, NamedTuple

SOURCE_INITIAL = "initial_odometer"
SOURCE_HISTORY_BEFORE = "history_before_month_start"
SOURCE_HISTORY_AFTER = "history_after_month_start"
SOURCE_FALLBACK = "estimated_fallback"

# A reading taken after the month boundary is only accepted as the baseline
# when it was taken this close to the boundary. Older history may have been
# purged by the recorder, and a mid-month reading would undercount the month.
MAX_DELAY_AFTER_BOUNDARY = timedelta(days=1)


class StateSnapshot(NamedTuple):
    """Minimal state-like object (raw state and the time it was last set)."""

    state: Any
    last_updated: datetime


class MonthBaseline(NamedTuple):
    """Odometer baseline for one calendar month."""

    month: date
    value: float | None
    source: str


def parse_odometer(value: Any) -> float | None:
    """Convert a raw state value to a finite float, or None if not numeric.

    'unknown', 'unavailable', empty strings and other non-numeric values
    return None.
    """
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def baseline_month(today: date, start_date: date, end_date: date) -> date | None:
    """Return the first day of the month that needs a recorder baseline.

    Monthly statistics refer to the calendar month of min(today, end_date).
    When the contract started on or after the 1st of that month (or has not
    started yet), the configured initial odometer is the baseline and None is
    returned.
    """
    first_of_month = min(today, end_date).replace(day=1)
    if start_date >= first_of_month:
        return None
    return first_of_month


def select_month_start_baseline(
    states: Iterable[Any],
    boundary: datetime,
    max_delay_after: timedelta = MAX_DELAY_AFTER_BOUNDARY,
) -> tuple[float | None, str]:
    """Select the odometer value at the month boundary.

    Preference order:
    1. The latest valid reading at or before the boundary (exact value).
    2. The earliest valid reading after the boundary, if it lies within
       max_delay_after of the boundary (close approximation).
    3. None with SOURCE_FALLBACK.

    Args:
        states: State-like objects with .state and .last_updated, in any order
        boundary: Timezone-aware start of the month
        max_delay_after: Maximum accepted distance of a post-boundary reading

    Returns:
        Tuple of (value or None, source label)
    """
    before: tuple[datetime, float] | None = None
    after: tuple[datetime, float] | None = None

    for state in states:
        if state is None:
            continue
        value = parse_odometer(state.state)
        if value is None:
            continue
        updated = state.last_updated
        if updated <= boundary:
            if before is None or updated >= before[0]:
                before = (updated, value)
        elif updated - boundary <= max_delay_after:
            if after is None or updated < after[0]:
                after = (updated, value)

    if before is not None:
        return before[1], SOURCE_HISTORY_BEFORE
    if after is not None:
        return after[1], SOURCE_HISTORY_AFTER
    return None, SOURCE_FALLBACK


def is_fallback_final(
    history_available: bool,
    now: datetime,
    boundary: datetime,
    max_delay_after: timedelta = MAX_DELAY_AFTER_BOUNDARY,
) -> bool:
    """Return True when retrying the history lookup cannot change the result.

    Once the history was read successfully and the window for post-boundary
    readings has closed, no new reading can qualify as the month baseline.
    After a recorder error, or while the window is still open, a retry may
    still find one.

    Args:
        history_available: Whether the recorder history was read without error
        now: Current timezone-aware time
        boundary: Timezone-aware start of the month
        max_delay_after: Maximum accepted distance of a post-boundary reading
    """
    return history_available and now > boundary + max_delay_after


def baseline_to_dict(entity_id: str, baseline: MonthBaseline) -> dict[str, Any]:
    """Serialize a baseline for persistent storage."""
    return {
        "entity_id": entity_id,
        "month": baseline.month.isoformat(),
        "value": baseline.value,
        "source": baseline.source,
    }


def baseline_from_dict(data: Any, entity_id: str) -> MonthBaseline | None:
    """Restore a stored baseline, or None if it is invalid or for another entity.

    Only baselines with a real value from history are restored; fallback
    entries are never trusted.
    """
    if not isinstance(data, dict) or data.get("entity_id") != entity_id:
        return None
    if data.get("source") not in (SOURCE_HISTORY_BEFORE, SOURCE_HISTORY_AFTER):
        return None
    value = parse_odometer(data.get("value"))
    if value is None:
        return None
    try:
        month = date.fromisoformat(data["month"])
    except (KeyError, TypeError, ValueError):
        return None
    if month.day != 1:
        return None
    return MonthBaseline(month=month, value=value, source=data["source"])
