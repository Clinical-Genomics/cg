from pydantic import BaseModel, Field


class OrderOpenUpdateRequest(BaseModel):
    delivered_analyses_count: int = Field(..., alias="deliveredAnalysesCount")
