"""Models for parsing excel files"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


class ApplicationVersionSchema(BaseModel):
    app_tag: str = Field(alias="App tag")
    version: int = Field(alias="Version")
    valid_from: datetime = Field(alias="Valid from")
    standard: int = Field(alias="Standard")
    priority: int = Field(alias="Priority")
    express: int = Field(alias="Express")
    research: int = Field(alias="Research")
    percent_kth: int = Field(alias="Percent kth")


class ApplicationSchema(BaseModel):
    comment: Optional[str]
    created_at: datetime
    description: str
    details: Optional[str]
    is_accredited: int
    is_archived: int
    is_external: int
    limitations: Optional[str]
    minimum_order: int
    percent_kth: Optional[int]
    percent_reads_guaranteed: Optional[int]
    prep_category: str
    priority_processing: int
    sample_amount: int
    sample_concentration: str
    sample_volume: str
    sequencing_depth: int
    tag: str
    target_reads: int
    turnaround_time: int

    @validator("comment", "details", "limitations")
    def convert_to_string(cls, value):
        if value is None:
            return ""
        return value

    @validator("percent_kth")
    def convert_to_number(cls, value):
        if value is None:
            return 80
        return value
