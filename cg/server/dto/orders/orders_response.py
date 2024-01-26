from datetime import datetime

from pydantic import BaseModel

from cg.constants import Pipeline


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: datetime
    workflow: Pipeline


class OrdersResponse(BaseModel):
    orders: list[Order]
