from .chat import router as chat_router
from .session import router as session_router

ROUTES = [chat_router, session_router]

__all__ = ["ROUTES"]
