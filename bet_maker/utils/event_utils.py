import time

from sqlalchemy import update

from models import AsyncSessionLocal, Bet


def update_event_dict(data: dict) -> dict:
    return {
        key: event for key, event in data.items()
        if time.time() < event.get("deadline")
    }


async def update_bet_status(event_id: str, status: int) -> None:
    async with AsyncSessionLocal() as db:
        async with db.begin():
            bet_for_update = (
                update(Bet)
                .where(Bet.event_id == event_id)
                .values(status=status)
                .execution_options(synchronize_session="fetch")
            )
            await db.execute(bet_for_update)
