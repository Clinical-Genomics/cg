from pydantic import BaseModel


class CaseConfig(BaseModel):
    case_id: str
    workflow: str
