"""Calculation utilities for Car Rental Tracker."""
from __future__ import annotations

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
        start_date, today, km_allowance_per_month, initial_odometer, current_odometer
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
    days_in_end_month = (end_date.replace(day=28) + relativedelta(days=4)).replace(day=1) - relativedelta(days=1)
    days_in_end_month = days_in_end_month.day
    fraction = delta.days / days_in_end_month
    return months + fraction


def calculate_monthly_stats(
    start_date: date,
    current_date: date,
    km_allowance_per_month: float,
    initial_odometer: float,
    current_odometer: float,
) -> dict[str, float]:
    """Calculate statistics for the current month.
    
    Args:
        start_date: Start date of the rental period
        current_date: Current date
        km_allowance_per_month: Monthly KM allowance
        initial_odometer: Initial odometer reading
        current_odometer: Current odometer reading
        
    Returns:
        Dictionary with monthly statistics
    """
    # Calculate which month we're in (1-indexed)
    months_elapsed = calculate_months_between(start_date, current_date)
    current_month_index = int(months_elapsed)
    
    # Calculate start of current rental month
    current_month_start = start_date + relativedelta(months=current_month_index)
    
    # For the first month, use the actual start date
    if current_month_index == 0:
        month_start_date = start_date
    else:
        month_start_date = current_month_start
    
    # Calculate expected odometer at start of this month
    expected_at_month_start = initial_odometer + (current_month_index * km_allowance_per_month)
    
    # Calculate driven this month
    total_driven = current_odometer - initial_odometer
    expected_driven_so_far = months_elapsed * km_allowance_per_month
    
    # Monthly driven is the portion driven in current month
    driven_this_month = max(total_driven - (current_month_index * km_allowance_per_month), 0)
    
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
