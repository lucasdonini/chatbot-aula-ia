import inspect
import time
from functools import wraps
from logging import Logger, getLogger
from typing import Callable


def log_execution_time[**P, R](
    function: Callable[P, R], logger: Logger | None = None
) -> Callable[P, R]:
    logger = logger or getLogger(function.__module__)

    if inspect.iscoroutinefunction(function):

        @wraps(function)
        async def wrapper_async(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            try:
                result = await function(*args, **kwargs)
                return result  # type: ignore[no-any-return]
            finally:
                end_time = time.perf_counter()
                elapsed_ms = round((end_time - start_time) * 1000)
                logger.debug(
                    "Function finished",
                    extra={
                        "details": {
                            "function": function.__name__,
                            "elapsed_ms": elapsed_ms,
                            "kind": "Async",
                        }
                    },
                )

        return wrapper_async  # type: ignore[return-value]
    else:

        @wraps(function)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.perf_counter()
            try:
                result = function(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                elapsed_ms = round((end_time - start_time) * 1000)
                logger.debug(
                    "Function finished",
                    extra={
                        "details": {
                            "function": function.__name__,
                            "elapsed_ms": elapsed_ms,
                            "kind": "Sync",
                        }
                    },
                )

        return wrapper
