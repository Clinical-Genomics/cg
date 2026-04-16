from pathlib import Path

from pydantic import BaseModel, field_validator


class FileDeliverable(BaseModel):
    """Specification for a general deliverables file."""

    id: str
    format: str
    path: str
    path_index: str | None = None
    step: str
    tag: str

    @field_validator("path", "path_index", mode="before")
    @classmethod
    def set_path_as_string(cls, file_path: str | Path) -> str | None:
        return str(Path(file_path)) if file_path else None


class WorkflowDeliverables(BaseModel):
    """Specification for workflow deliverables."""

    files: list[FileDeliverable]
