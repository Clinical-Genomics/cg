from pydantic import BaseModel

from cg.constants import Workflow
from cg.services.orders.order_status_service.dto.order_status_summary import OrderStatusSummary


class Order(BaseModel):
    customer_id: str
    ticket_id: int
    order_date: str
    order_id: int
    workflow: Workflow
    summary: OrderStatusSummary | None = None


class OrdersResponse(BaseModel):
    orders: list[Order]
