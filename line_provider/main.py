import decimal
import json
from typing import Optional

from fastapi import FastAPI, HTTPException
from kafka import KafkaProducer

from pydantic import BaseModel

from config import settings

app = FastAPI()


class UpdateEventStatus(BaseModel):
    state: int


class Event(BaseModel):
    event_id: str
    coefficient: Optional[decimal.Decimal] = None
    deadline: Optional[int] = None
    state: int = 1

    def dict(self, *args, **kwargs):
        original_dict = super().dict(*args, **kwargs)
        for key, value in original_dict.items():
            if isinstance(value, decimal.Decimal):
                original_dict[key] = round(float(value), 2)
        return original_dict


events: dict[str, Event] = {
}


async def send_event(data: dict) -> None:
    producer = KafkaProducer(bootstrap_servers=settings.KAFKA_URL,
                             value_serializer=lambda v: json.dumps(v).encode("utf-8"))
    producer.send("event",
                  {
                      key: event.dict()
                      for key, event in data.items()
                  }
                  )


@app.post("/api/v1/event/")
async def create_event(event: Event):
    if event.event_id in events:
        raise HTTPException(status_code=409, detail="The event already exists")
    events[event.event_id] = event
    for p_name, p_value in event.dict(exclude_unset=True).items():
        setattr(events[event.event_id], p_name, p_value)
    await send_event(events)
    return events


@app.get('/api/v1/event/{event_id}/')
async def get_event(event_id: str):
    if event_id in events:
        return events[event_id]
    raise HTTPException(status_code=404, detail="Event not found")


@app.post("/api/v1/event/{event_id}/")
async def update_event_status(event_id: str, event: UpdateEventStatus):
    if event_id not in events:
        raise HTTPException(status_code=404, detail="Event not found")
    events.get(event_id).state = event.state
    await send_event(events)
    return events
