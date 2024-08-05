from pydantic import BaseModel, Field


class OrderDeliveredUpdateRequest(BaseModel):
    delivered_analyses_count: int = Field(..., alias="deliveredAnalysesCount")
