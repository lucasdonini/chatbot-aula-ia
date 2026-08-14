import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:

    @app.exception_handler(Exception)
    async def handle_unexpected_exception(_: Request, exc: Exception) -> JSONResponse:
        logger.exception(
            "Unhandled error",
            exc_info=exc,
            extra={"details": {"session": app.state.session_id[:8]}},
        )

        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"},
        )
