from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class GoldOrderCreate(BaseModel):
    user_id: int
    step: str
    payment_method: Optional[str] = None
    amount: Optional[float] = None
    quantity_grams: Optional[float] = None


class GoldOrderResponse(BaseModel):
    id: int
    user_id: int
    step: str
    payment_method: Optional[str]
    amount: Optional[float]
    quantity_grams: Optional[float]
    created_at: datetime

    class Config:
        orm_mode = True
