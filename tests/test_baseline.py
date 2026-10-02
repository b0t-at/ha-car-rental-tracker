"""Tests for the month-start baseline selection (baseline.py)."""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest

from baseline import (
    MAX_DELAY_AFTER_BOUNDARY,
    SOURCE_FALLBACK,
    SOURCE_HISTORY_AFTER,
    SOURCE_HISTORY_BEFORE,
    MonthBaseline,
    StateSnapshot,
    baseline_from_dict,
    baseline_month,
    baseline_to_dict,
    is_fallback_final,
    parse_odometer,
    select_month_start_baseline,
)

BOUNDARY = datetime(2024, 3, 1, tzinfo=timezone.utc)
ENTITY = "sensor.car_odometer"


def snap(state, offset: timedelta) -> StateSnapshot:
    """Return a snapshot taken at BOUNDARY + offset."""
    return StateSnapshot(state, BOUNDARY + offset)


class TestParseOdometer:
    @pytest.mark.parametrize(
        ("raw", "expected"),
        [("12345", 12345.0), ("12345.6", 12345.6), (100, 100.0), (0.5, 0.5)],
    )
    def test_numeric_values_are_parsed(self, raw, expected):
        assert parse_odometer(raw) == expected

    @pytest.mark.parametrize(
        "raw", ["unknown", "unavailable", "", "abc", None, True, "nan", "inf"]
    )
    def test_non_numeric_values_return_none(self, raw):
        assert parse_odometer(raw) is None


class TestBaselineMonth:
    def test_contract_started_in_earlier_month_needs_baseline(self):
        assert baseline_month(
            date(2024, 3, 15), date(2024, 1, 10), date(2024, 12, 31)
        ) == date(2024, 3, 1)

    def test_contract_started_this_month_uses_initial_odometer(self):
        assert baseline_month(
            date(2024, 3, 15), date(2024, 3, 1), date(2024, 12, 31)
        ) is None
        assert baseline_month(
            date(2024, 3, 15), date(2024, 3, 10), date(2024, 12, 31)
        ) is None

    def test_before_contract_start_needs_no_baseline(self):
        assert baseline_month(
            date(2024, 1, 5), date(2024, 2, 1), date(2024, 12, 31)
        ) is None

    def test_after_contract_end_uses_final_contract_month(self):
        assert baseline_month(
            date(2025, 2, 10), date(2024, 1, 1), date(2024, 12, 31)
        ) == date(2024, 12, 1)


class TestSelectMonthStartBaseline:
    def test_latest_reading_before_boundary_wins(self):
        states = [
            snap("1000", -timedelta(days=3)),
            snap("1100", -timedelta(hours=1)),
            snap("1200", timedelta(hours=2)),
        ]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1100.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_order_of_states_does_not_matter(self):
        states = [
            snap("1200", timedelta(hours=2)),
            snap("1100", -timedelta(hours=1)),
            snap("1000", -timedelta(days=3)),
        ]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1100.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_reading_exactly_at_boundary_counts_as_before(self):
        states = [snap("1500", timedelta(0))]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1500.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_invalid_states_are_skipped(self):
        states = [
            snap("1100", -timedelta(hours=5)),
            snap("unavailable", -timedelta(hours=1)),
            snap("unknown", timedelta(minutes=5)),
        ]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1100.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_none_entries_are_ignored(self):
        states = [None, snap("1100", -timedelta(hours=1)), None]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1100.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_earliest_reading_shortly_after_boundary_is_used(self):
        states = [
            snap("1300", timedelta(hours=10)),
            snap("1250", timedelta(hours=3)),
        ]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1250.0,
            SOURCE_HISTORY_AFTER,
        )

    def test_reading_long_after_boundary_is_rejected(self):
        """A mid-month reading (e.g. after a recorder purge) is not a baseline."""
        states = [snap("1800", timedelta(days=11))]
        assert select_month_start_baseline(states, BOUNDARY) == (
            None,
            SOURCE_FALLBACK,
        )

    def test_reading_at_max_delay_is_accepted(self):
        states = [snap("1250", MAX_DELAY_AFTER_BOUNDARY)]
        assert select_month_start_baseline(states, BOUNDARY) == (
            1250.0,
            SOURCE_HISTORY_AFTER,
        )

    def test_custom_max_delay(self):
        states = [snap("1250", timedelta(hours=3))]
        assert select_month_start_baseline(
            states, BOUNDARY, max_delay_after=timedelta(hours=1)
        ) == (None, SOURCE_FALLBACK)

    def test_no_states_returns_fallback(self):
        assert select_month_start_baseline([], BOUNDARY) == (None, SOURCE_FALLBACK)

    def test_rollover_with_previous_and_current_reading(self):
        """Readings kept in memory across the boundary give the exact baseline."""
        previous = snap("2000", -timedelta(minutes=20))
        current = snap("2015", timedelta(minutes=30))
        assert select_month_start_baseline([previous, current], BOUNDARY) == (
            2000.0,
            SOURCE_HISTORY_BEFORE,
        )

    def test_works_with_non_utc_boundary(self):
        local_tz = timezone(timedelta(hours=1))
        local_boundary = datetime(2024, 3, 1, tzinfo=local_tz)  # 2024-02-29 23:00 UTC
        states = [
            StateSnapshot("900", datetime(2024, 2, 29, 22, 30, tzinfo=timezone.utc)),
            StateSnapshot("950", datetime(2024, 2, 29, 23, 30, tzinfo=timezone.utc)),
        ]
        assert select_month_start_baseline(states, local_boundary) == (
            900.0,
            SOURCE_HISTORY_BEFORE,
        )


class TestIsFallbackFinal:
    def test_final_after_window_when_history_was_read(self):
        now = BOUNDARY + MAX_DELAY_AFTER_BOUNDARY + timedelta(minutes=1)
        assert is_fallback_final(True, now, BOUNDARY) is True

    def test_not_final_while_window_is_open(self):
        now = BOUNDARY + timedelta(hours=3)
        assert is_fallback_final(True, now, BOUNDARY) is False

    def test_not_final_at_end_of_window(self):
        now = BOUNDARY + MAX_DELAY_AFTER_BOUNDARY
        assert is_fallback_final(True, now, BOUNDARY) is False

    def test_not_final_after_recorder_error(self):
        now = BOUNDARY + timedelta(days=10)
        assert is_fallback_final(False, now, BOUNDARY) is False

    def test_custom_max_delay(self):
        now = BOUNDARY + timedelta(hours=2)
        assert is_fallback_final(
            True, now, BOUNDARY, max_delay_after=timedelta(hours=1)
        ) is True


class TestBaselinePersistence:
    def test_round_trip(self):
        baseline = MonthBaseline(date(2024, 3, 1), 1234.5, SOURCE_HISTORY_BEFORE)
        data = baseline_to_dict(ENTITY, baseline)
        assert data == {
            "entity_id": ENTITY,
            "month": "2024-03-01",
            "value": 1234.5,
            "source": SOURCE_HISTORY_BEFORE,
        }
        assert baseline_from_dict(data, ENTITY) == baseline

    def test_other_entity_is_ignored(self):
        data = baseline_to_dict(
            ENTITY, MonthBaseline(date(2024, 3, 1), 1.0, SOURCE_HISTORY_BEFORE)
        )
        assert baseline_from_dict(data, "sensor.other") is None

    def test_fallback_source_is_not_restored(self):
        data = {
            "entity_id": ENTITY,
            "month": "2024-03-01",
            "value": 1.0,
            "source": SOURCE_FALLBACK,
        }
        assert baseline_from_dict(data, ENTITY) is None

    @pytest.mark.parametrize(
        "data",
        [
            None,
            [],
            {},
            {"entity_id": ENTITY, "source": SOURCE_HISTORY_BEFORE, "value": 1.0},
            {
                "entity_id": ENTITY,
                "month": "not-a-date",
                "value": 1.0,
                "source": SOURCE_HISTORY_BEFORE,
            },
            {
                "entity_id": ENTITY,
                "month": "2024-03-15",
                "value": 1.0,
                "source": SOURCE_HISTORY_BEFORE,
            },
            {
                "entity_id": ENTITY,
                "month": "2024-03-01",
                "value": None,
                "source": SOURCE_HISTORY_BEFORE,
            },
        ],
    )
    def test_invalid_data_is_ignored(self, data):
        assert baseline_from_dict(data, ENTITY) is None
