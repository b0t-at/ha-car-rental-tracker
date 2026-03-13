"""Calculation utilities for Car Rental Tracker."""
from __future__ import annotations

import calendar
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from typing import NamedTuple


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
) -> RentalStats:
    """Calculate all rental statistics.
    
    Args:
        start_date: Start date of the rental period
        end_date: End date of the rental period
        km_allowance_per_month: Monthly KM allowance
        initial_odometer: Initial odometer reading at delivery
        current_odometer: Current odometer reading
        overage_cost_per_km: Cost per KM for overage
        
    Returns:
        RentalStats: Container with all calculated statistics
    """
    today = date.today()
    
    # Calculate time-based values
    days_total = (end_date - start_date).days + 1
    days_elapsed = min((today - start_date).days + 1, days_total)
    days_remaining = max((end_date - today).days, 0)
    
    # Calculate total allowance based on contract duration
    months_total = calculate_months_between(start_date, end_date)
    km_allowed_total = km_allowance_per_month * months_total
    
    # Calculate driven KM
    total_driven_km = max(current_odometer - initial_odometer, 0)
    
    # Calculate remaining KM
    km_remaining = km_allowed_total - total_driven_km
    
    # Calculate progress percentages
    time_progress = (days_elapsed / days_total * 100) if days_total > 0 else 0
    km_progress = (total_driven_km / km_allowed_total * 100) if km_allowed_total > 0 else 0
    
    # Calculate projected KM at end of contract
    if days_elapsed > 0 and days_remaining >= 0:
        daily_average = total_driven_km / days_elapsed
        km_projected = total_driven_km + (daily_average * days_remaining)
    else:
        km_projected = total_driven_km
    
    # Calculate monthly statistics
    monthly_stats = calculate_monthly_stats(
        start_date, today, km_allowance_per_month, initial_odometer, current_odometer,
        odometer_at_month_start=odometer_at_month_start,
    )
    
    # Calculate overage and cost
    projected_overage_km = max(km_projected - km_allowed_total, 0)
    projected_cost = projected_overage_km * overage_cost_per_km
    
    # Determine status
    is_over_limit = total_driven_km > km_allowed_total
    is_projected_over = km_projected > km_allowed_total
    
    # Status logic: compare KM usage vs time progress
    if is_over_limit or km_progress >= 100:
        status = "critical"
    elif is_projected_over or km_progress > time_progress + 10:
        status = "warning"
    else:
        status = "ok"
    
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


def calculate_months_between(start_date: date, end_date: date) -> float:
    """Calculate the number of months between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of months (fractional)
    """
    delta = relativedelta(end_date, start_date)
    months = delta.years * 12 + delta.months
    # Add fractional month based on days
    days_in_end_month = calendar.monthrange(end_date.year, end_date.month)[1]
    fraction = delta.days / days_in_end_month if days_in_end_month > 0 else 0
    return months + fraction


def calculate_monthly_stats(
    start_date: date,
    current_date: date,
    km_allowance_per_month: float,
    initial_odometer: float,
    current_odometer: float,
    odometer_at_month_start: float | None = None,
) -> dict[str, float]:
    """Calculate statistics for the current month.
    
    Args:
        start_date: Start date of the rental period
        current_date: Current date
        km_allowance_per_month: Monthly KM allowance
        initial_odometer: Initial odometer reading
        current_odometer: Current odometer reading
        odometer_at_month_start: Odometer reading at the 1st of the current month
        
    Returns:
        Dictionary with monthly statistics
    """
    first_of_month = current_date.replace(day=1)

    # If the contract started this month, the configured initial odometer is the
    # authoritative baseline. Using recorder history from before the contract
    # would incorrectly count pre-contract driving.
    if start_date >= first_of_month:
        driven_this_month = max(current_odometer - initial_odometer, 0)
    # Use exact odometer difference since start of this calendar month when a
    # baseline reading is available from recorder history.
    elif odometer_at_month_start is not None:
        driven_this_month = max(current_odometer - odometer_at_month_start, 0)
    else:
        # Fallback: use daily average estimate when no stored month-start value
        total_driven = max(current_odometer - initial_odometer, 0)
        total_days_elapsed = (current_date - start_date).days + 1
        daily_average = total_driven / total_days_elapsed if total_days_elapsed > 0 else 0
        days_this_month = (current_date - first_of_month).days + 1
        driven_this_month = daily_average * days_this_month

    # Remaining this month
    remaining_this_month = max(km_allowance_per_month - driven_this_month, 0)
    
    return {
        "driven": driven_this_month,
        "remaining": remaining_this_month,
        "allowance": km_allowance_per_month,
    }


def calculate_daily_average(total_driven: float, days_elapsed: int) -> float:
    """Calculate daily average KM driven.
    
    Args:
        total_driven: Total KM driven so far
        days_elapsed: Number of days elapsed
        
    Returns:
        Daily average KM
    """
    if days_elapsed <= 0:
        return 0.0
    return total_driven / days_elapsed


def is_on_pace(time_progress: float, km_progress: float, tolerance: float = 5.0) -> bool:
    """Check if KM usage is on pace with time progress.
    
    Args:
        time_progress: Percentage of time elapsed
        km_progress: Percentage of KM used
        tolerance: Tolerance percentage (default 5%)
        
    Returns:
        True if on pace, False otherwise
    """
    return abs(km_progress - time_progress) <= tolerance
