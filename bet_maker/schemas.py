from pydantic import BaseModel, condecimal


class CreateBet(BaseModel):
    event_id: str
    amount: condecimal(gt=0)


class BetResponse(BaseModel):
    id: str
    event_id: str
    amount: condecimal(gt=0)
    status: int

    class Config:
        orm_mode = True
