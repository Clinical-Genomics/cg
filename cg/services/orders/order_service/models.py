from pydantic import BaseModel, Field, field_validator

from cg.constants import Workflow
from cg.server.dto.orders.orders_request import OrderSortField, SortOrder


class OrderQueryParams(BaseModel):
    page_size: int | None = Field(default=50)
    page: int | None = Field(default=1)
    sort_field: str | None = Field(default=OrderSortField.ORDER_DATE)
    sort_order: str | None = Field(default=SortOrder.ASC)
    search: str | None = None
    workflows: list[str] | None = []
    is_open: bool | None = None

    @field_validator("workflows", mode="before")
    def expand_balsamic_workflow(cls, value):
        """Include Balsamic UMI while preserving all selected workflows."""
        if value and Workflow.BALSAMIC in value and Workflow.BALSAMIC_UMI not in value:
            value = [*value, Workflow.BALSAMIC_UMI]
        return value
