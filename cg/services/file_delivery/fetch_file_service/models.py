from pathlib import Path

from pydantic import BaseModel


class CaseFile(BaseModel):
    case_id: str
    file_path: Path


class SampleFile(BaseModel):
    case_id: str
    sample_id: str
    file_path: Path


class DeliveryFiles(BaseModel):
    case_files: list[CaseFile] | None
    sample_files: list[SampleFile]
