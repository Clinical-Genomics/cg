from pydantic import BaseModel, validator
from typing import Optional
from dateutil.parser import parse as parse_datestr
from pathlib import Path


class TrailblazerAnalysis(BaseModel):
    id: int
    family: str
    case_id = Optional[str]

    version: Optional[str]
    logged_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    status: Optional[str]
    priority: Optional[str]
    out_dir: Optional[str]
    config_path: Optional[str]
    comment: Optional[str]
    is_deleted: Optional[bool]
    is_visible: Optional[bool]
    type: Optional[str]
    user_id: Optional[int]
    progress: Optional[float] = 0.0

    @validator("case_id")
    def inherit_family_value(cls, value, values):
        return values.get("family")

    @validator("logged_at", "started_at", "completed_at")
    def parse_str_to_datetime(cls, value):
        if value:
            return parse_datestr(value)

    @validator("out_dir", "config_path")
    def parse_str_to_path(cls, value):
        if value:
            return Path(value)

    class Config:
        extra = "allow"
        validate_all = True
        arbitrary_types_allowed = True
