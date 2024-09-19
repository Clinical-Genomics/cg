from pathlib import Path

from pydantic import BaseModel, Field


class DeliveryMetaData(BaseModel):
    customer_internal_id: str
    ticket_id: str


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
    case_files: list[CaseFile] | None
    sample_files: list[SampleFile] = Field(
        ..., min_length=1, description="At least one sample file is required for delivery."
    )
