from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field

from cg.constants import Workflow
from cg.constants.lims import LimsStatus
from cg.models.orders.constants import OrderType


class SortDirection(StrEnum):
    ASCENDING = "asc"
    DESCENDING = "desc"


class UnhandledSamplesSortBy(StrEnum):
    TICKET = "ticket"


class CollaboratorSamplesRequest(BaseModel):
    customer: str
    enquiry: str
    limit: int = 50
    order_type: OrderType | None = None


class SamplesRequest(BaseModel):
    status: str | None = None
    enquiry: str | None = None
    page: int = 1
    page_size: int | None = Field(50, alias="pageSize")


class SampleUpdate(BaseModel):
    internal_id: str
    lims_status: LimsStatus


class SamplesUpdateRequest(BaseModel):
    samples: list[SampleUpdate]


class UnhandledSamplesRequest(BaseModel):
    lims_status: LimsStatus
    page: int
    page_size: int
    search: str | None = None
    sort_by: UnhandledSamplesSortBy | None = None
    sort_order: SortDirection | None = None
    workflow: Workflow | Literal["unknown"] | None = None
