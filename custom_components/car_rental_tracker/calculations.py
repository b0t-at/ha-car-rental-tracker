"""Calculation utilities for Car Rental Tracker.

This module is intentionally free of Home Assistant imports so it can be
unit tested without Home Assistant installed.

Conventions:
    - The contract end date is inclusive (Jan 1 - Dec 31 is exactly 12 months).
    - Monthly statistics are based on calendar months (1st of month to today),
      clamped to the contract window.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import NamedTuple

from dateutil.relativedelta import relativedelta

STATUS_OK = "ok"
STATUS_WARNING = "warning"
STATUS_CRITICAL = "critical"

# KM progress may lead time progress by this many percentage points before
# the status changes to warning.
WARNING_PROGRESS_MARGIN = 10.0


class RentalStats(NamedTuple):
    """Container for rental statistics."""

    total_driven_km: float
    km_allowed: float
    km_remaining: float
    km_projected: float
    time_progress: float
    km_progress: float
    monthly_driven_km: float
    monthly_remaining_km: float
    monthly_allowance_km: float
    days_remaining: int
    days_elapsed: int
    days_total: int
    projected_overage_km: float
    projected_cost: float
    status: str
    is_over_limit: bool
    is_projected_over: bool


def calculate_rental_stats(
    start_date: date,
    end_date: date,
    km_allowance_per_month: float,
    initial_odometer: float,
    current_odometer: float,
    overage_cost_per_km: float,
    odometer_at_month_start: float | None = None,
    *,
    today: date | None = None,
) -> RentalStats:
    """Calculate all rental statistics.

    Args:
        start_date: Start date of the rental period
        end_date: End date of the rental period (inclusive)
        km_allowance_per_month: Monthly KM allowance
        initial_odometer: Initial odometer reading at delivery
        current_odometer: Current odometer reading
        overage_cost_per_km: Cost per KM for overage
        odometer_at_month_start: Odometer reading at the 1st of the calendar
            month of min(today, end_date), if known from recorder history
        today: Evaluation date (defaults to date.today()); pass the Home
            Assistant local date to avoid timezone mismatches

    Returns:
        RentalStats: Container with all calculated statistics
    """
    if today is None:
        today = date.today()

    has_started = today >= start_date

    # Time-based values (end date inclusive, so the start day counts as day 1)
    days_total = (end_date - start_date).days + 1
    if has_started:
        days_elapsed = min((today - start_date).days + 1, days_total)
        days_remaining = min(max((end_date - today).days, 0), days_total)
    else:
        days_elapsed = 0
        days_remaining = days_total

    # Total allowance based on the inclusive contract duration
    months_total = calculate_months_between(start_date, end_date + timedelta(days=1))
    km_allowed_total = km_allowance_per_month * months_total

    total_driven_km = max(current_odometer - initial_odometer, 0)
    km_remaining = km_allowed_total - total_driven_km

    time_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
    time_progress = min(max(time_progress, 0), 100)
    km_progress = (total_driven_km / km_allowed_total * 100) if km_allowed_total > 0 else 0

    # Linear projection to the end of the contract
    if days_elapsed > 0:
        daily_average = total_driven_km / days_elapsed
        km_projected = total_driven_km + (daily_average * days_remaining)
    else:
        km_projected = total_driven_km

    # Monthly statistics freeze at the final contract month after the end date
    monthly_stats = calculate_monthly_stats(
        start_date,
        min(today, end_date),
        km_allowance_per_month,
        initial_odometer,
        current_odometer,
        odometer_at_month_start=odometer_at_month_start,
    )

    projected_overage_km = max(km_projected - km_allowed_total, 0)
    projected_cost = projected_overage_km * overage_cost_per_km

    is_over_limit = total_driven_km > km_allowed_total
    is_projected_over = km_projected > km_allowed_total

    status = _determine_status(
        has_started, is_over_limit, is_projected_over, km_progress, time_progress
    )

    return RentalStats(
        total_driven_km=round(total_driven_km, 2),
        km_allowed=round(km_allowed_total, 2),
        km_remaining=round(km_remaining, 2),
        km_projected=round(km_projected, 2),
        time_progress=round(time_progress, 2),
        km_progress=round(km_progress, 2),
        monthly_driven_km=round(monthly_stats["driven"], 2),
        monthly_remaining_km=round(monthly_stats["remaining"], 2),
        monthly_allowance_km=round(km_allowance_per_month, 2),
        days_remaining=days_remaining,
        days_elapsed=days_elapsed,
        days_total=days_total,
        projected_overage_km=round(projected_overage_km, 2),
        projected_cost=round(projected_cost, 2),
        status=status,
        is_over_limit=is_over_limit,
        is_projected_over=is_projected_over,
    )


def _determine_status(
    has_started: bool,
    is_over_limit: bool,
    is_projected_over: bool,
    km_progress: float,
    time_progress: float,
) -> str:
    """Determine the overall status by comparing KM usage to time progress."""
    if not has_started:
        return STATUS_OK
    if is_over_limit or km_progress >= 100:
        return STATUS_CRITICAL
    if is_projected_over or km_progress > time_progress + WARNING_PROGRESS_MARGIN:
        return STATUS_WARNING
    return STATUS_OK


def calculate_months_between(start_date: date, end_date: date) -> float:
    """Calculate the number of months between two dates (end date exclusive).

    Whole months are counted with relativedelta. The leftover days are divided
    by the length of the month-long period in which they actually fall
    (anchor to next anchor, both computed from start_date), so the result
    never decreases when end_date moves later.

    Args:
        start_date: Start date
        end_date: End date (exclusive)

    Returns:
        Number of months (fractional)
    """
    delta = relativedelta(end_date, start_date)
    months = delta.years * 12 + delta.months
    anchor = start_date + relativedelta(months=months)
    next_anchor = start_date + relativedelta(months=months + 1)
    period_days = (next_anchor - anchor).days
    fraction = (end_date - anchor).days / period_days if period_days > 0 else 0
    return months + fraction


def calculate_monthly_stats(
    start_date: date,
    current_date: date,
    km_allowance_per_month: float,
    initial_odometer: float,
    current_odometer: float,
    odometer_at_month_start: float | None = None,
) -> dict[str, float]:
    """Calculate statistics for the calendar month of current_date.

    Args:
        start_date: Start date of the rental period
        current_date: Evaluation date, already clamped to the contract end date
        km_allowance_per_month: Monthly KM allowance
        initial_odometer: Initial odometer reading
        current_odometer: Current odometer reading
        odometer_at_month_start: Odometer reading at the 1st of the month of
            current_date

    Returns:
        Dictionary with "driven" and "remaining" KM for the month
    """
    first_of_month = current_date.replace(day=1)

    # If the contract started this month (or has not started yet), the
    # configured initial odometer is the authoritative baseline. Using recorder
    # history from before the contract would incorrectly count pre-contract
    # driving.
    if start_date >= first_of_month:
        driven_this_month = max(current_odometer - initial_odometer, 0)
    # Use exact odometer difference since start of this calendar month when a
    # baseline reading is available from recorder history.
    elif odometer_at_month_start is not None:
        driven_this_month = max(current_odometer - odometer_at_month_start, 0)
    else:
        # Fallback: estimate from the contract's daily average
        total_driven = max(current_odometer - initial_odometer, 0)
        total_days_elapsed = (current_date - start_date).days + 1
        daily_average = total_driven / total_days_elapsed if total_days_elapsed > 0 else 0
        days_this_month = (current_date - first_of_month).days + 1
        driven_this_month = daily_average * days_this_month

    remaining_this_month = max(km_allowance_per_month - driven_this_month, 0)

    return {
        "driven": driven_this_month,
        "remaining": remaining_this_month,
    }
