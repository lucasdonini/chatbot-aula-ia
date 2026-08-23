from collections.abc import Callable, Mapping
from contextlib import AbstractContextManager
from typing import Protocol, runtime_checkable


@runtime_checkable
class Logger(Protocol):
    def debug(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None: ...

    def info(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None: ...

    def warning(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None: ...

    def error(
        self,
        message: str,
        *,
        details: Mapping[str, object] | None = None,
    ) -> None: ...

    def exception(
        self,
        message: str,
        *,
        exception: BaseException,
        details: Mapping[str, object] | None = None,
    ) -> None: ...


type LoggerFactory = Callable[[str], Logger]
type TraceContextFactory = Callable[[str], AbstractContextManager[None]]
type InteractionIncrementer = Callable[[], int]
