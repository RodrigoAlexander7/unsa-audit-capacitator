from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine


class SqlAlchemyDatabaseProbe:
    """Adaptador del puerto DatabaseProbe usando SQLAlchemy async."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def is_up(self) -> bool:
        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return True
        except Exception:
            return False
