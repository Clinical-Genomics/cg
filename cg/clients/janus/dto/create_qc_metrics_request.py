"""Post request model for JanusAPI."""

from enum import StrEnum

from pydantic import BaseModel

from cg.constants import Workflow


class SupportedWorkflow(StrEnum):
    BALSAMIC: str = Workflow.BALSAMIC


class SupportedPrepCategory(StrEnum):
    TGA: str = "tga"
    WGS: str = "wgs"


class FilePathAndTag(BaseModel):
    """Model for the file path and its associated tag."""

    file_path: str
    tag: str


class CreateQCMetricsRequest(BaseModel):
    """Model for the qc collection request."""

    case_id: str
    sample_ids: list[str]
    files: list[FilePathAndTag]
    workflow: SupportedWorkflow
    prep_category: SupportedPrepCategory | None
