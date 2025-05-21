from pydantic import BaseModel

from cg.constants import Workflow


class StartParameters(BaseModel):
    case_id: str


class RunParameters(BaseModel):
    case_id: str


class CaseConfig(BaseModel):
    case_id: str
    workflow: Workflow
