from pydantic import BaseModel

from cg.constants import Workflow


class CaseConfig(BaseModel):
    case_id: str
    workflow: Workflow

    def get_session_id(self) -> str | None:
        # This will be set by the NextflowCaseConfig
        return None

    def get_workflow_id(self) -> str | None:
        # This will be set by the NextflowCaseConfig
        return None
