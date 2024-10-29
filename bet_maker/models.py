from sqlalchemy import Column, String, Integer, DECIMAL

from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from config import settings

Base = declarative_base()
engine = create_async_engine(settings.db_url, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class Bet(Base):
    __tablename__ = "bets"

    id = Column(String, primary_key=True, index=True)
    event_id = Column(String, nullable=False)
    amount = Column(DECIMAL(10, 2))
    status = Column(Integer, default=1)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
