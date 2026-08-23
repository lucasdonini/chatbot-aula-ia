from datetime import datetime, timezone

from app.infrastructure.agents._core.prompting.temporal_context import (
    build_temporal_context,
)
from app.infrastructure.clock import FixedClock

APP_TIMEZONE = "America/Sao_Paulo"


def test_temporal_context_uses_fixed_local_time_and_dynamic_periods() -> None:
    clock = FixedClock(
        datetime(2026, 4, 4, 15, 30, tzinfo=timezone.utc),
        APP_TIMEZONE,
    )

    context = build_temporal_context(clock)

    assert "2026-04-04 12:30:00 -03" in context
    assert '| "mês passado"     | 2026-03-01 | 2026-04-01 |' in context
    assert '| "semana passada"  | 2026-03-23 | 2026-03-30 |' in context
    assert "Suponto que hoje" not in context


def test_temporal_context_is_rebuilt_when_clock_changes() -> None:
    first_clock = FixedClock(
        datetime(2026, 4, 4, 15, 0, tzinfo=timezone.utc),
        APP_TIMEZONE,
    )
    second_clock = FixedClock(
        datetime(2026, 5, 4, 15, 0, tzinfo=timezone.utc),
        APP_TIMEZONE,
    )
    first_context = build_temporal_context(first_clock)

    second_context = build_temporal_context(second_clock)

    assert "2026-04-01" in first_context
    assert "2026-05-01" in second_context
