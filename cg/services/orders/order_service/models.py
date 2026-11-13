from typing import Annotated

from pydantic import BaseModel, BeforeValidator, Field

from cg.constants import Workflow
from cg.server.dto.orders.orders_request import OrderSortField, SortOrder


def expand_balsamic_workflow(value):
    """Include Balsamic UMI while preserving all selected workflows."""
    if value and Workflow.BALSAMIC in value and Workflow.BALSAMIC_UMI not in value:
        value = [*value, Workflow.BALSAMIC_UMI]
    return value


class OrderQueryParams(BaseModel):
    page_size: int | None = Field(default=50)
    page: int | None = Field(default=1)
    sort_field: str | None = Field(default=OrderSortField.ORDER_DATE)
    sort_order: str | None = Field(default=SortOrder.ASC)
    search: str | None = None
    workflows: Annotated[list[str] | None, BeforeValidator(expand_balsamic_workflow)] = []
    is_open: bool | None = None
