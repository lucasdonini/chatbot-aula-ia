import json
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI

from app.api.middleware.exception_handler import register_exception_handlers
from app.application.exceptions import (
    AmbiguousTransactionError,
    InvalidTransactionCommandError,
    NoTransactionChangesError,
    TransactionConflictError,
    TransactionNotFoundError,
)
from app.application.ports.logger import Logger


@pytest.mark.asyncio
async def test_unexpected_exception_is_forwarded_to_logger() -> None:
    app = FastAPI()
    app.state.session_id = "session-123"
    logger = MagicMock(spec=Logger)
    register_exception_handlers(app, logger)
    exception = RuntimeError("failure")

    handler = app.exception_handlers[Exception]
    response = await handler(MagicMock(), exception)

    assert response.status_code == 500
    logger.exception.assert_called_once_with(
        "Unhandled error",
        exception=exception,
        details={"session": "session-"},
    )


@pytest.mark.asyncio
async def test_timeout_is_logged_without_unexpected_exception_traceback() -> None:
    app = FastAPI()
    logger = MagicMock(spec=Logger)
    register_exception_handlers(app, logger)
    exception = TimeoutError()

    handler = app.exception_handlers[TimeoutError]
    response = await handler(MagicMock(), exception)

    assert response.status_code == 504
    logger.warning.assert_called_once_with(
        "Request timed out",
        details={"exception_type": "TimeoutError"},
    )
    logger.exception.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("exception", "handler_type", "status_code"),
    [
        (NoTransactionChangesError(), InvalidTransactionCommandError, 422),
        (TransactionNotFoundError(), TransactionNotFoundError, 404),
        (AmbiguousTransactionError(), TransactionConflictError, 409),
    ],
)
async def test_application_errors_are_translated(
    exception: Exception, handler_type: type[Exception], status_code: int
) -> None:
    app = FastAPI()
    logger = MagicMock(spec=Logger)
    register_exception_handlers(app, logger)

    handler = app.exception_handlers[handler_type]
    response = await handler(MagicMock(), exception)
    content = json.loads(response.body)

    assert response.status_code == status_code
    assert content["code"] == exception.code
    assert content["detail"] == exception.public_message
    logger.exception.assert_not_called()


@pytest.mark.asyncio
async def test_unexpected_exception_without_session_id_is_still_handled() -> None:
    app = FastAPI()
    logger = MagicMock(spec=Logger)
    register_exception_handlers(app, logger)
    exception = RuntimeError("failure")

    handler = app.exception_handlers[Exception]
    response = await handler(MagicMock(), exception)

    assert response.status_code == 500
    logger.exception.assert_called_once_with(
        "Unhandled error",
        exception=exception,
        details={"session": ""},
    )
