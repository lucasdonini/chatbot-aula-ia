from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


class SystemClock:
    def __init__(self, timezone_name: str) -> None:
        self._timezone = ZoneInfo(timezone_name)

    def now(self) -> datetime:
        return datetime.now(timezone.utc)

    def local_now(self) -> datetime:
        return self.now().astimezone(self._timezone)

    def today(self) -> date:
        return self.local_now().date()


class FixedClock:
    def __init__(self, fixed: datetime, timezone_name: str) -> None:
        if fixed.tzinfo is None:
            raise ValueError("FixedClock requires a timezone-aware datetime.")
        self._fixed = fixed.astimezone(timezone.utc)
        self._timezone = ZoneInfo(timezone_name)

    def now(self) -> datetime:
        return self._fixed

    def local_now(self) -> datetime:
        return self._fixed.astimezone(self._timezone)

    def today(self) -> date:
        return self.local_now().date()
