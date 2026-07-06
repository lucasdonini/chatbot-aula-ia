import logging
from typing import Optional

from beanie import init_beanie
from pymongo import AsyncMongoClient
from pymongo.monitoring import (
    CommandFailedEvent,
    CommandListener,
    CommandStartedEvent,
    CommandSucceededEvent,
    register,
)

from src.model.chat_session import ChatSession

from .settings import settings

logger = logging.getLogger(__name__)


IGNORED_COMMANDS = {
    "ismaster",
    "ping",
    "hello",
    "buildinfo",
    "saslstart",
    "saslcontinue",
}


class LoggingMongoCommandListener(CommandListener):
    """
    Listener to log every query made to the
    mongo database to improve maintanability
    """

    def started(self, event: CommandStartedEvent) -> None:
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                "Mongo command started",
                extra={
                    "details": {
                        "command": event.command_name,
                        "database": event.database_name,
                        "query": str(event.command),
                    }
                },
            )

    def succeeded(self, event: CommandSucceededEvent) -> None:
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                "Mongo command succeeded",
                extra={
                    "details": {
                        "command": event.command_name,
                        "database": event.database_name,
                        "elapsed_ms": round(event.duration_micros / 1000, 2),
                    }
                },
            )

    def failed(self, event: CommandFailedEvent) -> None:
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                "Mongo command failed",
                extra={
                    "details": {
                        "command": event.command_name,
                        "database": event.database_name,
                        "error": str(event.failure),
                    }
                },
            )


register(LoggingMongoCommandListener())


class MongoManager:
    _client: Optional[AsyncMongoClient] = None

    @classmethod
    async def init_database(cls) -> None:
        """Initialize connection and map classes"""
        if cls._client is None:
            cls._client = AsyncMongoClient(settings.mongodb_uri.get_secret_value())
            await init_beanie(
                database=cls._client[settings.mongodb_dbname.get_secret_value()],
                document_models=[ChatSession],
            )
            logger.debug("MongoDB initialized")
