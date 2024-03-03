from sqlalchemy import Column, Integer
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, declared_attr, sessionmaker

from core.config import settings


class PreBase:
    @declared_attr
    def __tablename__(cls):
        return f'azucafe_{cls.__name__.lower()}'

    id = Column(Integer, primary_key=True)


Base = declarative_base(cls=PreBase)

AsyncEngine = create_async_engine(settings.database_url, echo=False)

AsyncSessionLocal = sessionmaker(
    AsyncEngine,
    expire_on_commit=False,
    class_=AsyncSession,
    future=True,
)


async def get_async_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
