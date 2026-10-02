"""Tests for the Car Rental Tracker calculation helpers.

All tests pass an explicit ``today`` so they are deterministic.
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from calculations import (
    STATUS_CRITICAL,
    STATUS_OK,
    STATUS_WARNING,
    calculate_monthly_stats,
    calculate_months_between,
    calculate_rental_stats,
)

YEAR_START = date(2024, 1, 1)
YEAR_END = date(2024, 12, 31)  # 2024 is a leap year: 366 days


def _stats(
    today: date,
    current_odometer: float,
    *,
    start_date: date = YEAR_START,
    end_date: date = YEAR_END,
    allowance: float = 1000.0,
    initial_odometer: float = 0.0,
    cost_per_km: float = 0.1,
    odometer_at_month_start: float | None = None,
):
    """Call calculate_rental_stats with common defaults."""
    return calculate_rental_stats(
        start_date=start_date,
        end_date=end_date,
        km_allowance_per_month=allowance,
        initial_odometer=initial_odometer,
        current_odometer=current_odometer,
        overage_cost_per_km=cost_per_km,
        odometer_at_month_start=odometer_at_month_start,
        today=today,
    )


class TestMonthsBetween:
    """Tests for calculate_months_between (end date exclusive)."""

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (date(2024, 1, 1), date(2024, 4, 1), 3.0),
            (date(2024, 11, 1), date(2025, 2, 1), 3.0),
            (date(2024, 1, 1), date(2024, 1, 1), 0.0),
            (date(2024, 1, 1), date(2025, 1, 1), 12.0),
            (date(2024, 1, 15), date(2025, 1, 15), 12.0),
        ],
    )
    def test_whole_months(self, start: date, end: date, expected: float) -> None:
        """Whole-month spans give exact integers."""
        assert calculate_months_between(start, end) == expected

    def test_partial_month_uses_length_of_its_own_period(self) -> None:
        """Leftover days are measured against the period they fall in."""
        # Jan 15 -> Feb 1: 17 days of the Jan 15 - Feb 15 period (31 days)
        assert calculate_months_between(date(2024, 1, 15), date(2024, 2, 1)) == (
            pytest.approx(17 / 31)
        )
        # Feb 1 -> Feb 15 (leap year): 14 of 29 days
        assert calculate_months_between(date(2024, 2, 1), date(2024, 2, 15)) == (
            pytest.approx(14 / 29)
        )

    def test_partial_month_with_clamped_anchor(self) -> None:
        """Start on the 31st: the anchor is clamped to the end of February."""
        # Jan 31 + 1 month = Feb 29; next anchor Mar 31 -> 1 day of 31
        assert calculate_months_between(date(2024, 1, 31), date(2024, 3, 1)) == (
            pytest.approx(1 + 1 / 31)
        )

    @pytest.mark.parametrize(
        "start", [date(2024, 1, 1), date(2024, 1, 15), date(2024, 1, 30), date(2024, 1, 31)]
    )
    def test_monotonic_over_end_dates(self, start: date) -> None:
        """The month count strictly increases as the end date moves later."""
        previous = calculate_months_between(start, start)
        for offset in range(1, 800):
            current = calculate_months_between(start, start + timedelta(days=offset))
            assert current > previous, start + timedelta(days=offset)
            previous = current


class TestAllowance:
    """Tests for the total KM allowance with an inclusive end date."""

    @pytest.mark.parametrize(
        ("start", "end", "expected"),
        [
            (date(2024, 1, 1), date(2024, 12, 31), 12000.0),
            (date(2024, 2, 1), date(2024, 2, 29), 1000.0),
            (date(2024, 1, 15), date(2025, 1, 14), 12000.0),
            (date(2024, 1, 1), date(2026, 12, 31), 36000.0),
        ],
    )
    def test_inclusive_end_date(self, start: date, end: date, expected: float) -> None:
        """A contract ending the day before an anniversary is a whole number of months."""
        stats = _stats(start, 0.0, start_date=start, end_date=end)
        assert stats.km_allowed == expected

    def test_partial_last_month(self) -> None:
        """Jan 1 - Jan 15 (inclusive) is 15 of 31 days."""
        stats = _stats(YEAR_START, 0.0, end_date=date(2024, 1, 15))
        assert stats.km_allowed == round(1000.0 * 15 / 31, 2)


class TestTimeValues:
    """Tests for days and time progress."""

    def test_before_start(self) -> None:
        """Before the contract starts nothing has elapsed and status is ok."""
        stats = _stats(
            date(2024, 2, 15),
            100.0,
            start_date=date(2024, 3, 1),
            end_date=date(2025, 2, 28),
            initial_odometer=100.0,
        )
        assert stats.days_total == 365
        assert stats.days_elapsed == 0
        assert stats.days_remaining == 365
        assert stats.time_progress == 0.0
        assert stats.km_projected == 0.0
        assert stats.monthly_driven_km == 0.0
        assert stats.monthly_remaining_km == 1000.0
        assert stats.status == STATUS_OK
        assert stats.is_projected_over is False

    def test_start_day(self) -> None:
        """The start day counts as the first elapsed day."""
        stats = _stats(YEAR_START, 0.0)
        assert stats.days_total == 366
        assert stats.days_elapsed == 1
        assert stats.days_remaining == 365

    def test_mid_contract(self) -> None:
        """Day 183 of 366 is exactly 50 percent."""
        stats = _stats(date(2024, 7, 1), 0.0)
        assert stats.days_elapsed == 183
        assert stats.days_remaining == 183
        assert stats.time_progress == 50.0

    def test_last_day(self) -> None:
        """On the end date the whole contract has elapsed."""
        stats = _stats(YEAR_END, 0.0)
        assert stats.days_elapsed == 366
        assert stats.days_remaining == 0
        assert stats.time_progress == 100.0

    def test_after_end(self) -> None:
        """After the end date values are clamped and monthly stats freeze."""
        stats = _stats(date(2025, 3, 10), 13000.0, odometer_at_month_start=12500.0)
        assert stats.days_elapsed == 366
        assert stats.days_remaining == 0
        assert stats.time_progress == 100.0
        assert stats.km_projected == 13000.0
        assert stats.projected_overage_km == 1000.0
        assert stats.projected_cost == 100.0
        # December (last contract month) driven against its baseline
        assert stats.monthly_driven_km == 500.0
        assert stats.monthly_remaining_km == 500.0
        assert stats.status == STATUS_CRITICAL

    def test_default_today(self) -> None:
        """Without an explicit date the calculation uses date.today()."""
        today = date.today()
        stats = calculate_rental_stats(
            start_date=today,
            end_date=today + timedelta(days=9),
            km_allowance_per_month=1000.0,
            initial_odometer=0.0,
            current_odometer=0.0,
            overage_cost_per_km=0.1,
        )
        assert stats.days_elapsed == 1
        assert stats.days_remaining == 9


class TestProjectionAndStatus:
    """Tests for projection, overage and status thresholds."""

    def test_on_pace_is_ok(self) -> None:
        """Driving exactly at allowance pace projects to the allowance."""
        stats = _stats(date(2024, 7, 1), 6000.0)
        assert stats.total_driven_km == 6000.0
        assert stats.km_remaining == 6000.0
        assert stats.km_progress == 50.0
        assert stats.km_projected == 12000.0
        assert stats.projected_overage_km == 0.0
        assert stats.projected_cost == 0.0
        assert stats.is_projected_over is False
        assert stats.status == STATUS_OK

    def test_under_pace_is_ok(self) -> None:
        """Driving below pace is ok."""
        stats = _stats(date(2024, 7, 1), 3000.0)
        assert stats.km_projected == 6000.0
        assert stats.status == STATUS_OK

    def test_projected_over_is_warning(self) -> None:
        """Driving above pace projects an overage and warns."""
        stats = _stats(date(2024, 7, 1), 7320.0)
        assert stats.km_projected == 14640.0
        assert stats.projected_overage_km == 2640.0
        assert stats.projected_cost == 264.0
        assert stats.is_projected_over is True
        assert stats.is_over_limit is False
        assert stats.status == STATUS_WARNING

    def test_allowance_used_up_is_critical(self) -> None:
        """Reaching 100 percent of the allowance is critical."""
        stats = _stats(date(2024, 7, 1), 12000.0)
        assert stats.km_progress == 100.0
        assert stats.km_remaining == 0.0
        assert stats.is_over_limit is False
        assert stats.status == STATUS_CRITICAL

    def test_over_limit_is_critical(self) -> None:
        """Exceeding the allowance is critical with a negative remaining value."""
        stats = _stats(date(2024, 7, 1), 12500.0)
        assert stats.km_remaining == -500.0
        assert stats.is_over_limit is True
        assert stats.status == STATUS_CRITICAL

    def test_odometer_below_initial_is_zero_driven(self) -> None:
        """A current reading below the initial reading counts as zero."""
        stats = _stats(date(2024, 7, 1), 50.0, initial_odometer=100.0)
        assert stats.total_driven_km == 0.0
        assert stats.km_projected == 0.0

    def test_zero_allowance_without_driving(self) -> None:
        """A zero allowance does not divide by zero."""
        stats = _stats(date(2024, 7, 1), 0.0, allowance=0.0)
        assert stats.km_allowed == 0.0
        assert stats.km_progress == 0.0
        assert stats.monthly_allowance_km == 0.0
        assert stats.monthly_remaining_km == 0.0
        assert stats.status == STATUS_OK

    def test_zero_allowance_with_driving(self) -> None:
        """Any driving with a zero allowance is over the limit."""
        stats = _stats(date(2024, 7, 1), 100.0, allowance=0.0)
        assert stats.km_progress == 0.0
        assert stats.km_remaining == -100.0
        assert stats.is_over_limit is True
        assert stats.status == STATUS_CRITICAL


class TestMonthlyStats:
    """Tests for calculate_monthly_stats branches."""

    def test_contract_started_this_month_uses_initial_odometer(self) -> None:
        """The initial odometer wins over a pre-contract recorder baseline."""
        stats = calculate_monthly_stats(
            date(2024, 3, 10), date(2024, 3, 20), 1000.0, 5000.0, 5300.0,
            odometer_at_month_start=4000.0,
        )
        assert stats == {"driven": 300.0, "remaining": 700.0}

    def test_contract_starting_on_first_uses_initial_odometer(self) -> None:
        """A start on the 1st counts as starting this month."""
        stats = calculate_monthly_stats(
            date(2024, 3, 1), date(2024, 3, 1), 1000.0, 5000.0, 5050.0,
            odometer_at_month_start=4900.0,
        )
        assert stats == {"driven": 50.0, "remaining": 950.0}

    def test_uses_month_start_baseline(self) -> None:
        """A recorder baseline gives the exact distance this month."""
        stats = calculate_monthly_stats(
            date(2024, 1, 1), date(2024, 3, 20), 1000.0, 0.0, 2600.0,
            odometer_at_month_start=2200.0,
        )
        assert stats == {"driven": 400.0, "remaining": 600.0}

    def test_baseline_above_current_is_zero(self) -> None:
        """A baseline above the current reading counts as zero driven."""
        stats = calculate_monthly_stats(
            date(2024, 1, 1), date(2024, 3, 20), 1000.0, 0.0, 2000.0,
            odometer_at_month_start=2100.0,
        )
        assert stats == {"driven": 0.0, "remaining": 1000.0}

    def test_month_allowance_exceeded_remaining_is_zero(self) -> None:
        """Remaining never goes below zero."""
        stats = calculate_monthly_stats(
            date(2024, 1, 1), date(2024, 3, 20), 1000.0, 0.0, 4000.0,
            odometer_at_month_start=2500.0,
        )
        assert stats == {"driven": 1500.0, "remaining": 0.0}

    def test_fallback_daily_average(self) -> None:
        """Without a baseline the contract daily average is used."""
        # 41 days elapsed (Jan 1 - Feb 10), 820 km -> 20 km/day, 10 days in Feb
        stats = calculate_monthly_stats(
            date(2024, 1, 1), date(2024, 2, 10), 1000.0, 0.0, 820.0,
        )
        assert stats["driven"] == pytest.approx(200.0)
        assert stats["remaining"] == pytest.approx(800.0)

    def test_rental_stats_pass_through(self) -> None:
        """calculate_rental_stats exposes the monthly values rounded."""
        stats = _stats(date(2024, 3, 20), 2600.0, odometer_at_month_start=2200.0)
        assert stats.monthly_driven_km == 400.0
        assert stats.monthly_remaining_km == 600.0
        assert stats.monthly_allowance_km == 1000.0
