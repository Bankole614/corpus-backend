from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


from sqlalchemy import inspect, text


def _migrate_columns(connection) -> None:
    inspector = inspect(connection)
    if "users" in inspector.get_table_names():
        columns = [col["name"] for col in inspector.get_columns("users")]
        statements = []
        if "email" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN email VARCHAR")
        if "hashed_password" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN hashed_password VARCHAR")
        if "full_name" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN full_name VARCHAR")
        if "avatar_url" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN avatar_url VARCHAR")
        if "google_id" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN google_id VARCHAR")
        if "is_active" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT 1")
        if "is_admin" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT 0")
        if "updated_at" not in columns:
            statements.append("ALTER TABLE users ADD COLUMN updated_at DATETIME")
        for stmt in statements:
            connection.execute(text(stmt))


async def init_db() -> None:
    """Create tables if they don't exist, and ensure updated columns exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_migrate_columns)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
