from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    def now(self) -> datetime: ...

    def local_now(self) -> datetime: ...

    def today(self) -> date: ...
