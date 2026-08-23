import logging
from unittest.mock import MagicMock

import pytest

from app.infrastructure.execution_time_logger import log_execution_time


def test_logs_sync_execution_time_when_function_fails() -> None:
    logger = MagicMock(spec=logging.Logger)

    def fail() -> None:
        raise RuntimeError("failure")

    decorated = log_execution_time(fail, logger)

    with pytest.raises(RuntimeError, match="failure"):
        decorated()

    logger.debug.assert_called_once()
    assert logger.debug.call_args.kwargs["extra"]["details"]["kind"] == "Sync"


@pytest.mark.asyncio
async def test_logs_async_execution_time_when_function_fails() -> None:
    logger = MagicMock(spec=logging.Logger)

    async def fail() -> None:
        raise RuntimeError("failure")

    decorated = log_execution_time(fail, logger)

    with pytest.raises(RuntimeError, match="failure"):
        await decorated()

    logger.debug.assert_called_once()
    assert logger.debug.call_args.kwargs["extra"]["details"]["kind"] == "Async"
