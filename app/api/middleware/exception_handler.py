from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.application.ports.logger import Logger


def register_exception_handlers(app: FastAPI, logger: Logger) -> None:

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
        logger.exception(
            "Unhandled error",
            exception=exc,
            details={"session": app.state.session_id[:8]},
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
