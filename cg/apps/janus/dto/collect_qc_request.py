"""Post request model for JanusAPI."""

from pydantic import BaseModel


class FilePathAndTag(BaseModel):
    """Model for the file path and its associated tag."""

    file_path: str
    tag: str


class CollectQCRequest(BaseModel):
    """Model for the qc collection request."""

    case_id: str
    sample_ids: list[str]
    files: list[FilePathAndTag]
    workflow: str
    prep_category: str
