from typing import Awaitable, Callable

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles

from .api.middleware.exception_handler import register_exception_handlers
from .api.routes import ROUTES
from .infrastructure.logger import bind_session_context, create_logger
from .infrastructure.paths import FRONTEND
from .lifespan import lifespan

app = FastAPI(
    title="Assessor.IA API",
    summary="Multi-agent chatbot API",
    version="2.0.0",
    description=(
        "## Assessor.IA\n\n"
        "API responsible for hosting Assessor.IA's multi-agent system.\n"
        "Assessor.IA is a chatbot that helps you with your finance and agenda."
    ),
    lifespan=lifespan,
)

register_exception_handlers(app, create_logger(register_exception_handlers.__module__))


@app.middleware("http")
async def logging_context_middleware(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
) -> Response:
    session_id = getattr(request.app.state, "session_id", "")
    with bind_session_context(session_id):
        return await call_next(request)


for router in ROUTES:
    app.include_router(router, prefix="/api")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "Assessor.IA API is up and running!"}


@app.get("/")
def root() -> FileResponse:
    return FileResponse(FRONTEND / "index.html")


app.mount("/", StaticFiles(directory=FRONTEND))
