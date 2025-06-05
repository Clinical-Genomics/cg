from pydantic import BaseModel

from cg.constants import Workflow


class StartParameters(BaseModel):
    pass


class RunParameters(BaseModel):
    pass


class CaseConfig(BaseModel):
    case_id: str
    workflow: Workflow
