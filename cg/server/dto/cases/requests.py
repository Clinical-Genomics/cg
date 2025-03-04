from pydantic import BaseModel, Field

from cg.constants.constants import CaseActions


class CasesRequest(BaseModel):
    action: CaseActions | None = None
    enquiry: str | None = None
    page: int = 1
    page_size: int = Field(50, alias="pageSize")
