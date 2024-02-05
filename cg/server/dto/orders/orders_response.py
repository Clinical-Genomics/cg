from pydantic import BaseModel

from cg.constants import Workflow


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: str
    order_id: int
    workflow: Workflow


class OrdersResponse(BaseModel):
    orders: list[Order]
