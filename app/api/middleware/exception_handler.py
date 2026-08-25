from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.exceptions import (
    ApplicationError,
    InvalidTransactionCommandError,
    TransactionConflictError,
    TransactionNotFoundError,
)
from app.application.ports.logger import Logger, SessionContextFactory


def register_exception_handlers(
    app: FastAPI,
    *,
    logger: Logger,
    session_context_factory: SessionContextFactory,
) -> None:
    def _get_session_id(request: Request) -> str:
        return getattr(request.state, "session_id", "")

    def application_error_response(
        error: ApplicationError,
        status_code: int,
        request: Request,
    ) -> JSONResponse:
        session_id = _get_session_id(request)
        with session_context_factory(session_id):
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
        request: Request, exc: InvalidTransactionCommandError
    ) -> JSONResponse:
        return application_error_response(exc, 422, request)

    @app.exception_handler(TransactionNotFoundError)
    async def handle_transaction_not_found(
        request: Request, exc: TransactionNotFoundError
    ) -> JSONResponse:
        return application_error_response(exc, 404, request)

    @app.exception_handler(TransactionConflictError)
    async def handle_transaction_conflict(
        request: Request, exc: TransactionConflictError
    ) -> JSONResponse:
        return application_error_response(exc, 409, request)

    @app.exception_handler(ApplicationError)
    async def handle_application_error(
        request: Request, exc: ApplicationError
    ) -> JSONResponse:
        return application_error_response(exc, 400, request)

    @app.exception_handler(TimeoutError)
    async def handle_timeout(request: Request, exc: TimeoutError) -> JSONResponse:
        session_id = _get_session_id(request)
        with session_context_factory(session_id):
            logger.warning(
                "Request timed out",
                details={"exception_type": type(exc).__name__},
            )
            return JSONResponse(
                status_code=504,
                content={
                    "detail": "A operação excedeu o tempo limite. Tente novamente."
                },
            )

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(
        request: Request, exc: Exception
    ) -> JSONResponse:
        session_id = _get_session_id(request)
        with session_context_factory(session_id):
            logger.exception(
                "Unhandled error",
                exception=exc,
            )

            return JSONResponse(
                status_code=500,
                content={"detail": "Internal Server Error"},
            )
