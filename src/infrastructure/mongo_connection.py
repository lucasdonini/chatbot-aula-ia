import logging

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

    def started(self, event: CommandStartedEvent):
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                f"MONGO QUERY EXECUTED [{event.command_name}] - "
                f"Database: {event.database_name} - "
                f"Query: {event.command}"
            )

    def succeeded(self, event: CommandSucceededEvent):
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                f"MONGO QUERY SUCCEEDED [{event.command_name}] - "
                f"Database: {event.database_name} - "
                f"Execution time: {event.duration_micros / 1_000} s"
            )

    def failed(self, event: CommandFailedEvent):
        if event.command_name.lower() not in IGNORED_COMMANDS:
            logger.debug(
                f"MONGO QUERY EXECUTED [{event.command_name}] - "
                f"Database: {event.database_name} - "
                f"Error: {event.failure}"
            )


register(LoggingMongoCommandListener())


class MongoManager:
    _client = None

    @classmethod
    async def init_database(cls):
        """Initialize connection and map classes"""
        if cls._client is None:
            cls._client = AsyncMongoClient(settings.mongodb_uri)
            await init_beanie(
                database=cls._client[settings.mongodb_dbname],
                document_models=[ChatSession],
            )
            logger.info("MongoDB Beanie initialized successfully")
