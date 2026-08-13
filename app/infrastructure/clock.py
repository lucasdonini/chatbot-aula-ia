from datetime import date, datetime, timezone
from typing import Protocol
from zoneinfo import ZoneInfo

from .settings import settings


class Clock(Protocol):
    def now(self) -> datetime: ...

    def local_now(self) -> datetime: ...

    def today(self) -> date: ...


class SystemClock:
    def __init__(self, timezone_name: str | None = None) -> None:
        self._timezone = ZoneInfo(timezone_name or settings.app_timezone)

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def local_now(self) -> datetime:
        return self.now().astimezone(self._timezone)

    def today(self) -> date:
        return self.local_now().date()


class FixedClock:
    def __init__(self, fixed: datetime, timezone_name: str | None = None) -> None:
        if fixed.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime.")
        self._fixed = fixed.astimezone(timezone.utc)
        self._timezone = ZoneInfo(timezone_name or settings.app_timezone)

    def now(self) -> datetime:
        return self._fixed

    def local_now(self) -> datetime:
        return self._fixed.astimezone(self._timezone)

    def today(self) -> date:
        return self.local_now().date()


_clock: Clock = SystemClock()


def get_clock() -> Clock:
    return _clock


def set_clock(clock: Clock) -> None:
    global _clock
    _clock = clock
