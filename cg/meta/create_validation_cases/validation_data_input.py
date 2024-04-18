"""Model for the validation case data input."""

from pydantic import BaseModel


class ValidationDataInput(BaseModel):
    case_name: str
    case_id: str
    delivery: str | None = None
    data_analysis: str | None = None
