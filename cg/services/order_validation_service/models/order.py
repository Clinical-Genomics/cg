from pydantic import BaseModel, Field

from cg.constants import DataDelivery
from cg.constants.constants import Workflow
from cg.models.orders.orderform_schema import OrderCase

TICKET_PATTERN = r"^#\d{4,}"


class Order(BaseModel):
    workflow: Workflow
    cases: list[OrderCase]
    comment: str | None = None
    connect_to_ticket: bool = False
    customer: str
    delivery_type: DataDelivery
    name: str
    skip_reception_control: bool = False
    ticket_number: str | None = Field(None, pattern=TICKET_PATTERN)
