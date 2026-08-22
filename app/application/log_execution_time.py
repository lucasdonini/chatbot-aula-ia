import time
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar, cast

from app.application.ports.logger import Logger

P = ParamSpec("P")
R = TypeVar("R")


class _HasLogger(Protocol):
    _logger: Logger


def log_execution_time(
    function: Callable[P, Awaitable[R]],
) -> Callable[P, Awaitable[R]]:
    @wraps(function)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        if not args:
            raise TypeError("log_execution_time requires an instance method")

        owner = cast(_HasLogger, args[0])
        start_time = time.perf_counter()
        try:
            return await function(*args, **kwargs)
        finally:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000)
            owner._logger.debug(
                "Function finished",
                details={
                    "function": function.__name__,
                    "elapsed_ms": elapsed_ms,
                    "kind": "Async",
                },
            )

    return wrapper
