from pydantic import BaseModel

from cg.constants import Workflow
from cg.services.orders.order_summary_service.dto.order_summary import OrderSummary


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: str
    id: int
    is_delivered: bool
    workflow: Workflow
    summary: OrderSummary | None = None


class OrdersResponse(BaseModel):
    orders: list[Order]
    total_count: int
