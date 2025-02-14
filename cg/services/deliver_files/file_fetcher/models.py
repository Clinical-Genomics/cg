from pathlib import Path

from pydantic import BaseModel


class DeliveryMetaData(BaseModel):
    case_id: str
    customer_internal_id: str
    ticket_id: str
    delivery_path: Path | None = None


class CaseFile(BaseModel):
    case_id: str
    case_name: str
    file_path: Path


class SampleFile(BaseModel):
    case_id: str
    sample_id: str
    sample_name: str
    file_path: Path


class DeliveryFiles(BaseModel):
    delivery_data: DeliveryMetaData
    case_files: list[CaseFile]
    sample_files: list[SampleFile]
