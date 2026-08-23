from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    InvalidTransactionCommandError,
    TransactionConflictError,
    TransactionNotFoundError,
)
from app.application.ports.logger import Logger


def register_exception_handlers(app: FastAPI, logger: Logger) -> None:

    def application_error_response(
        error: ApplicationError, status_code: int
    ) -> JSONResponse:
        logger.warning(
            "Application error",
            details={"error_code": error.code, "status_code": status_code},
        )
        return JSONResponse(
            status_code=status_code,
            content={"code": error.code, "detail": error.public_message},
        )

    @app.exception_handler(InvalidTransactionCommandError)
    async def handle_invalid_transaction_command(
        _: Request, exc: InvalidTransactionCommandError
    ) -> JSONResponse:
        return application_error_response(exc, 422)

    @app.exception_handler(TransactionNotFoundError)
    async def handle_transaction_not_found(
        _: Request, exc: TransactionNotFoundError
    ) -> JSONResponse:
        return application_error_response(exc, 404)

    @app.exception_handler(TransactionConflictError)
    async def handle_transaction_conflict(
        _: Request, exc: TransactionConflictError
    ) -> JSONResponse:
        return application_error_response(exc, 409)

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        _: Request, exc: ApplicationError
    ) -> JSONResponse:
        return application_error_response(exc, 400)

    @app.exception_handler(TimeoutError)
    async def handle_timeout(_: Request, exc: TimeoutError) -> JSONResponse:
        logger.warning(
            "Request timed out",
            details={"exception_type": type(exc).__name__},
        )
        return JSONResponse(
            status_code=504,
            content={"detail": "A operação excedeu o tempo limite. Tente novamente."},
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        session_id = getattr(app.state, "session_id", "")
        logger.exception(
            "Unhandled error",
            exception=exc,
            details={"session": session_id[:8]},
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
