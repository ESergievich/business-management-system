from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings


class DatabaseHelper:
    """
    Helper class for managing an asynchronous SQLAlchemy database engine
    and session factory.

    This class simplifies creating an async engine, generating sessions,
    and properly disposing of the engine when no longer needed.

    Attributes:
        engine (AsyncEngine): The asynchronous SQLAlchemy engine instance.
        session_factory (async_sessionmaker[AsyncSession]): Factory for creating async sessions.
    """

    def __init__(
        self,
        url: str,
        *,
        echo: bool,
        echo_pool: bool,
        pool_size: int,
        max_overflow: int,
    ) -> None:
        """
        Initialize the DatabaseHelper with database connection settings.

        Args:
            url (str): Database connection URL, e.g., 'postgresql+asyncpg://user:pass@host/dbname'.
            echo (bool): If True, SQLAlchemy will log all SQL statements.
            echo_pool (bool): If True, logs pool checkouts/checkins.
            pool_size (int): The size of the database connection pool.
            max_overflow (int): Maximum number of connections to allow in overflow.

        Returns:
            None
        """
        self.engine: AsyncEngine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """
        Dispose of the database engine and release all pooled connections.

        This should be called when the application is shutting down
        to clean up resources properly.

        Returns:
            None
        """
        await self.engine.dispose()

    async def session_getter(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Async generator that provides a database session.

        Usage example with FastAPI dependency injection:
            async def get_db(session: AsyncSession = Depends(db_helper.session_getter)):
                ...

        Yields:
            AsyncSession: An asynchronous SQLAlchemy session.
        """
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(settings.db.url),
    echo=settings.db.echo,
    echo_pool=settings.db.echo_pool,
    pool_size=settings.db.pool_size,
    max_overflow=settings.db.max_overflow,
)
