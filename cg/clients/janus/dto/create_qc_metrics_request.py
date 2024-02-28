"""Post request model for JanusAPI."""

from pydantic import BaseModel

from cg.constants import PrepCategory, Workflow


class FilePathAndTag(BaseModel):
    """Model for the file path and its associated tag."""

    file_path: str
    tag: str


class CreateQCMetricsRequest(BaseModel):
    """Model for the qc collection request."""

    case_id: str
    sample_ids: list[str]
    files: list[FilePathAndTag]
    workflow: Workflow
    prep_category: PrepCategory
