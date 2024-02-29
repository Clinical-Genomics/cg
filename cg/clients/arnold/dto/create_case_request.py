"""Create case request for the arnold api client."""

from pydantic import BaseModel


class CreateCaseRequest(BaseModel):
    case_id: str
    case_info: dict
