from datetime import datetime, timezone

import pytest

from app.agents.temporal_context import build_temporal_context
from app.infrastructure.clock import FixedClock, get_clock, set_clock


@pytest.fixture(autouse=True)
def restore_clock() -> None:
    original_clock = get_clock()
    yield
    set_clock(original_clock)


def test_temporal_context_uses_fixed_local_time_and_dynamic_periods() -> None:
    set_clock(FixedClock(datetime(2026, 4, 4, 15, 30, tzinfo=timezone.utc)))

    context = build_temporal_context()

    assert "2026-04-04 12:30:00 -03" in context
    assert '| "mês passado"     | 2026-03-01 | 2026-04-01 |' in context
    assert '| "semana passada"  | 2026-03-23 | 2026-03-30 |' in context
    assert "Suponto que hoje" not in context


def test_temporal_context_is_rebuilt_when_clock_changes() -> None:
    set_clock(FixedClock(datetime(2026, 4, 4, 15, 0, tzinfo=timezone.utc)))
    first_context = build_temporal_context()
    set_clock(FixedClock(datetime(2026, 5, 4, 15, 0, tzinfo=timezone.utc)))

    second_context = build_temporal_context()

    assert "2026-04-01" in first_context
    assert "2026-05-01" in second_context
