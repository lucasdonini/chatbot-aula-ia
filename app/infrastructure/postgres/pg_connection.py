from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)


def build_async_postgres_url(database_url: str) -> URL:
    return make_url(database_url).set(drivername="postgresql+asyncpg")


def build_sync_postgres_url(database_url: str) -> URL:
    return make_url(database_url).set(drivername="postgresql+psycopg")


class PostgresManager:
    def __init__(self, database_url: str) -> None:
        self._engine: AsyncEngine = create_async_engine(
            build_async_postgres_url(database_url),
            pool_pre_ping=True,
        )
        self.session_factory = async_sessionmaker(
            bind=self._engine,
            autoflush=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        await self._engine.dispose()
