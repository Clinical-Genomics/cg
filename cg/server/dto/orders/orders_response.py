from datetime import datetime

from pydantic import BaseModel


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: datetime


class OrdersResponse(BaseModel):
    orders: list[Order]
