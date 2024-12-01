from datetime import date, datetime

from pydantic import BaseModel


class PredictIn(BaseModel):
    record_id: int
    transaction_id: int
    ip: str
    device_id: float
    device_type: str
    tran_code: int
    mcc: int
    client_id: int
    card_type: str
    pin_inc_count: int
    card_status: str
    datetime: datetime
    sum: float
    oper_type: str
    expiration_date: date
    balance: float


class PredictOut(BaseModel):
    pred: float
