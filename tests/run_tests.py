"""
Standalone test runner for car rental tracker calculations.
This bypasses Home Assistant dependencies by importing only the calculations module.
"""
import sys
import os

# Add parent directory to path to import the calculations module directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import the calculations module directly
import importlib.util
spec = importlib.util.spec_from_file_location(
    "calculations",
    os.path.join(os.path.dirname(__file__), '../custom_components/car_rental_tracker/calculations.py')
)
calculations = importlib.util.module_from_spec(spec)
spec.loader.exec_module(calculations)

# Now import the functions we need
calculate_rental_stats = calculations.calculate_rental_stats
calculate_months_between = calculations.calculate_months_between
calculate_monthly_stats = calculations.calculate_monthly_stats
calculate_daily_average = calculations.calculate_daily_average
is_on_pace = calculations.is_on_pace

# Now run the tests
import pytest
from datetime import date


class TestCalculateMonthsBetween:
    """Tests for calculate_months_between function."""

    def test_exact_months(self):
        """Test calculation with exact month boundaries."""
        start = date(2024, 1, 1)
        end = date(2024, 4, 1)
        assert calculate_months_between(start, end) == pytest.approx(3.0, abs=0.1)

    def test_partial_month(self):
        """Test calculation with partial month."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 15)
        result = calculate_months_between(start, end)
        assert 0.4 < result < 0.5  # Approximately half month

    def test_year_boundary(self):
        """Test calculation across year boundary."""
        start = date(2023, 11, 1)
        end = date(2024, 2, 1)
        assert calculate_months_between(start, end) == pytest.approx(3.0, abs=0.1)

    def test_same_date(self):
        """Test calculation with same start and end date."""
        start = date(2024, 1, 1)
        end = date(2024, 1, 1)
        assert calculate_months_between(start, end) == pytest.approx(0.0, abs=0.01)


class TestCalculateDailyAverage:
    """Tests for calculate_daily_average function."""

    def test_normal_usage(self):
        """Test normal daily average calculation."""
        assert calculate_daily_average(100.0, 10) == pytest.approx(10.0)

    def test_zero_days(self):
        """Test with zero days elapsed."""
        assert calculate_daily_average(50.0, 0) == pytest.approx(0.0)

    def test_fractional_result(self):
        """Test with result requiring decimal."""
        result = calculate_daily_average(100.0, 7)
        assert result == pytest.approx(14.286, abs=0.01)


class TestIsOnPace:
    """Tests for is_on_pace function."""

    def test_exactly_on_pace(self):
        """Test when KM and time progress are equal."""
        assert is_on_pace(50.0, 50.0) is True

    def test_within_tolerance(self):
        """Test when within default tolerance."""
        assert is_on_pace(50.0, 54.0) is True
        assert is_on_pace(50.0, 46.0) is True

    def test_outside_tolerance(self):
        """Test when outside default tolerance."""
        assert is_on_pace(50.0, 60.0) is False
        assert is_on_pace(50.0, 40.0) is False

    def test_custom_tolerance(self):
        """Test with custom tolerance value."""
        assert is_on_pace(50.0, 60.0, tolerance=15.0) is True
        assert is_on_pace(50.0, 40.0, tolerance=15.0) is True


class TestCalculateRentalStats:
    """Tests for calculate_rental_stats function."""

    def test_start_of_contract(self):
        """Test calculations at contract start."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=10000.0,
            overage_cost_per_km=0.25,
        )

        assert stats.total_driven_km == pytest.approx(0.0)
        assert stats.km_progress == pytest.approx(0.0)
        assert stats.km_projected >= 0.0
        assert stats.status == "ok"

    def test_mid_contract_on_pace(self):
        """Test calculations mid-contract when on pace."""
        # Contract: Jan 1 to Dec 31, 2024
        # 6 months in (June 30), driven 6000 km (exactly on pace)
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=16000.0,  # Driven 6000 km
            overage_cost_per_km=0.25,
        )

        assert stats.total_driven_km == pytest.approx(6000.0)
        # Should have approximately 12000 km allowed for full year
        assert stats.km_allowed == pytest.approx(12000.0, abs=100)
        assert stats.status in ["ok", "warning"]  # Depends on exact calculation

    def test_over_allowance(self):
        """Test when driver has exceeded allowance."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=25000.0,  # Driven 15000 km
            overage_cost_per_km=0.25,
        )

        assert stats.total_driven_km == pytest.approx(15000.0)
        assert stats.is_over_limit is True
        assert stats.status == "critical"
        assert stats.km_remaining < 0

    def test_projected_overage(self):
        """Test projected overage calculations."""
        # Early in contract but driving way too much
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=14000.0,  # Driven 4000 km in first month
            overage_cost_per_km=0.50,
        )

        assert stats.total_driven_km == pytest.approx(4000.0)
        # If continuing at this pace, should be projected over
        if stats.is_projected_over:
            assert stats.projected_overage_km > 0
            assert stats.projected_cost > 0
            assert stats.projected_cost == pytest.approx(stats.projected_overage_km * 0.50)

    def test_time_vs_km_progress(self):
        """Test comparison of time vs KM progress."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=16000.0,
            overage_cost_per_km=0.25,
        )

        # Both progress values should be between 0 and 100
        assert 0 <= stats.time_progress <= 100
        assert 0 <= stats.km_progress <= 150  # Can exceed 100 if over limit

    def test_contract_ended(self):
        """Test calculations after contract has ended."""
        stats = calculate_rental_stats(
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=20000.0,
            overage_cost_per_km=0.25,
        )

        assert stats.days_remaining == 0
        assert stats.time_progress >= 100
        assert stats.total_driven_km == pytest.approx(10000.0)


class TestCalculateMonthlyStats:
    """Tests for calculate_monthly_stats function."""

    def test_first_month(self):
        """Test monthly stats in first month of contract."""
        stats = calculate_monthly_stats(
            start_date=date(2024, 1, 1),
            current_date=date(2024, 1, 15),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=10500.0,
            odometer_at_month_start=10000.0,
        )

        assert stats["driven"] == pytest.approx(500.0)
        assert stats["remaining"] == pytest.approx(500.0)
        assert stats["allowance"] == pytest.approx(1000.0)

    def test_second_month(self):
        """Test monthly stats in second month."""
        stats = calculate_monthly_stats(
            start_date=date(2024, 1, 1),
            current_date=date(2024, 2, 15),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=11500.0,
            odometer_at_month_start=11000.0,
        )

        # Should show stats for second rental month
        assert stats["allowance"] == pytest.approx(1000.0)
        # Driven since 1st Feb = 11500 - 11000 = 500
        assert stats["driven"] == pytest.approx(500.0)

    def test_over_monthly_allowance(self):
        """Test when current month allowance exceeded."""
        stats = calculate_monthly_stats(
            start_date=date(2024, 1, 1),
            current_date=date(2024, 1, 15),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=11500.0,
            odometer_at_month_start=10000.0,
        )

        assert stats["driven"] == pytest.approx(1500.0)
        assert stats["remaining"] == pytest.approx(0.0)  # Should not go negative

    def test_contract_started_this_month_uses_initial_odometer(self):
        """Test that pre-contract history is ignored when the rental started this month."""
        stats = calculate_monthly_stats(
            start_date=date(2024, 2, 10),
            current_date=date(2024, 2, 15),
            km_allowance_per_month=1000.0,
            initial_odometer=12000.0,
            current_odometer=12300.0,
            odometer_at_month_start=11800.0,
        )

        # Monthly driven should only include distance since the contract started.
        assert stats["driven"] == pytest.approx(300.0)
        assert stats["remaining"] == pytest.approx(700.0)

    def test_fallback_without_month_start(self):
        """Test fallback to daily average when no month-start odometer."""
        stats = calculate_monthly_stats(
            start_date=date(2024, 1, 1),
            current_date=date(2024, 1, 15),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=10500.0,
        )

        # Without odometer_at_month_start, uses daily average fallback
        assert stats["driven"] > 0
        assert stats["allowance"] == pytest.approx(1000.0)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_negative_driven(self):
        """Test when current odometer is less than initial (shouldn't happen but handle it)."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=9500.0,  # Less than initial
            overage_cost_per_km=0.25,
        )

        # Should handle gracefully, probably show 0 driven
        assert stats.total_driven_km == pytest.approx(0.0)

    def test_very_short_contract(self):
        """Test with a very short contract period."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 1, 7),  # 1 week
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=10100.0,
            overage_cost_per_km=0.25,
        )

        assert stats.total_driven_km == pytest.approx(100.0)
        # Should still calculate correctly for short period
        assert stats.days_total == 7

    def test_zero_allowance(self):
        """Test with zero KM allowance (edge case)."""
        # This is an invalid configuration, but should not crash
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=0.0,
            initial_odometer=10000.0,
            current_odometer=10100.0,
            overage_cost_per_km=0.25,
        )

        # Should handle division by zero
        assert stats.km_progress >= 0

    def test_zero_overage_cost(self):
        """Test with zero overage cost."""
        stats = calculate_rental_stats(
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            km_allowance_per_month=1000.0,
            initial_odometer=10000.0,
            current_odometer=25000.0,  # Way over
            overage_cost_per_km=0.0,
        )

        assert stats.projected_cost == pytest.approx(0.0)
        # Even with overage, cost is 0
        assert stats.is_over_limit is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
