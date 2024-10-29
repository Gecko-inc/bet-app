import asyncio
import time
from typing import List
from uuid import uuid4

from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI, Depends, HTTPException
import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from utils.event_utils import update_event_dict, update_bet_status
from models import get_db, Bet
from schemas import CreateBet, BetResponse

app = FastAPI()
events: dict[str, dict] = {
}


async def consume():
    consumer = AIOKafkaConsumer(
        "event",
        bootstrap_servers=settings.KAFKA_URL,
        group_id="bet-maker-1",
        auto_offset_reset="earliest",
        value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    )
    await consumer.start()
    try:
        async for message in consumer:
            for key, val in message.value.items():
                if key in events:
                    await update_bet_status(key, val.get("state", 1))
                events[key] = val
    finally:
        await consumer.stop()


@app.on_event("startup")
async def startup_event():
    time.sleep(5)
    asyncio.create_task(consume())


@app.get('/api/v1/event/')
async def get_event():
    return update_event_dict(events)


@app.post("/api/v1/bet/", response_model=BetResponse)
async def create_bet(bet: CreateBet, db: AsyncSession = Depends(get_db)):
    if update_event_dict(events).get(bet.event_id):
        new_bet = Bet(
            id=str(uuid4()),
            amount=bet.amount,
            event_id=bet.event_id
        )
        db.add(
            new_bet
        )
        await db.commit()
        await db.refresh(new_bet)
        return new_bet
    else:
        raise HTTPException(status_code=404, detail="Event does not exist")


@app.get("/api/v1/bets/", response_model=List[BetResponse])
async def get_all_bet(db: AsyncSession = Depends(get_db)):
    all_bet = await db.execute(select(Bet))

    return all_bet.scalars().all()
