import inspect
import time
from functools import wraps
from logging import Logger, getLogger
from typing import Callable, Optional, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")


def log_execution_time(
    function: Callable[P, R], logger: Optional[Logger] = None
) -> Callable[P, R]:
    """
    Decorator to track and log execution time of
    IO functions (like database accesses) or LLM calls.
    Works with both sync and async functions
    """
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
                exec_time = end_time - start_time
                logger.debug(
                    f"[METRIC] IO/LLM Async - Function '{function.__name__}' "
                    f"finished in {exec_time:.4f} seconds."
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
                exec_time = end_time - start_time
                logger.debug(
                    f"[METRIC] IO/LLM Sync - Function '{function.__name__}' "
                    f"finished in {exec_time:.4f} seconds."
                )

        return wrapper
