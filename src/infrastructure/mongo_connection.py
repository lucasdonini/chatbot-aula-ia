import logging

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from src.model.chat_session import ChatSession

from .settings import settings

logger = logging.getLogger(__name__)


class MongoManager:
    _client = None

    @classmethod
    async def init_database(cls):
        """Initialize connection and map classes"""
        if cls._client is None:
            cls._client = AsyncIOMotorClient(settings.mongodb_uri)
            await init_beanie(
                database=cls._client[settings.mongodb_dbname],
                document_models=[ChatSession],
            )
            logger.info("MongoDB Beanie initialized successfully")
