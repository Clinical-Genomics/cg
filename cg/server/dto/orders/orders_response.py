from datetime import datetime

from pydantic import BaseModel


class Order(BaseModel):
    customer_id: int
    ticket_id: int
    order_date: datetime


class OrdersResponse(BaseModel):
    orders: list[Order]
