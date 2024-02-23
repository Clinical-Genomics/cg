from pydantic import BaseModel

from cg.constants import Workflow
from cg.services.orders.order_summary_service.summary import OrderSummary


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: str
    order_id: int
    workflow: Workflow
    summary: OrderSummary | None = None


class OrdersResponse(BaseModel):
    orders: list[Order]
