from pydantic import BaseModel, Field, field_validator

from cg.constants import Workflow
from cg.server.dto.orders.orders_request import OrderSortField, SortOrder


class OrderQueryParams(BaseModel):
    page_size: int | None = 50
    page: int | None = 1
    sort_field: str | None = Field(default=OrderSortField.ORDER_DATE)
    sort_order: str | None = Field(default=SortOrder.DESC)
    search: str | None = None
    workflows: list[str] | None = []
    is_open: bool | None = None

    @field_validator("workflows", mode="before")
    def expand_balsamic_workflow(cls, value):
        if value and Workflow.BALSAMIC in value:
            value = list(
                set(value) | {Workflow.BALSAMIC, Workflow.BALSAMIC_UMI, Workflow.BALSAMIC_QC}
            )
        return value
