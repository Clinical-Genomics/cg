from pydantic import BaseModel

from cg.constants import Workflow


class CaseConfig(BaseModel):
    case_id: str
    workflow: Workflow
