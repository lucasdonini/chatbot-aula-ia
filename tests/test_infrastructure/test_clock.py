from datetime import datetime, timezone

import pytest

from src.infrastructure.clock import FixedClock, SystemClock, get_clock, set_clock


@pytest.fixture(autouse=True)
def restore_clock() -> None:
    original_clock = get_clock()
    yield
    set_clock(original_clock)


def test_system_clock_returns_utc_aware_datetime() -> None:
    now = SystemClock().now()

    assert now.tzinfo is timezone.utc


def test_fixed_clock_returns_configured_instant() -> None:
    fixed = datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc)
    clock = FixedClock(fixed)
    local_now = clock.local_now()

    assert clock.now() == fixed
    assert local_now.hour == 12
    assert str(local_now.tzinfo) == "America/Sao_Paulo"
    assert clock.today().isoformat() == "2026-08-12"


def test_fixed_clock_rejects_naive_datetime() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        FixedClock(datetime(2026, 8, 12, 15, 0))
