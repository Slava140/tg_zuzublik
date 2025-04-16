from contextlib import asynccontextmanager

from sqlalchemy import String, BigInteger, Integer
from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine, AsyncSession

from src.config import settings

engine = create_async_engine(settings.database_url)
async_session = async_sessionmaker(engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    ...


class Item(Base):
    __tablename__ = 'items'

    id: Mapped[int] = mapped_column(BigInteger().with_variant(Integer, 'sqlite'), primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    url: Mapped[str] = mapped_column(String(255))
    xpath: Mapped[str] = mapped_column(String(255))
    price: Mapped[int | None]


@asynccontextmanager
async def async_db_session() -> AsyncSession:
    async with async_session() as session:
        yield session


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
