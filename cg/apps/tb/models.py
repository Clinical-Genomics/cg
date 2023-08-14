import datetime as dt
from pathlib import Path
from typing import Optional

from dateutil.parser import parse as parse_datestr
from pydantic.v1 import BaseModel, validator
from pydantic import field_validator, ConfigDict


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
    data_analysis: Optional[str]
    ticket: Optional[str]
    uploaded_at: Optional[str]

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @validator("case_id")
    def inherit_family_value(cls, value: str, values: dict) -> str:
        return values.get("family")

    @field_validator("logged_at", "started_at", "completed_at")
    @classmethod
    def parse_str_to_datetime(cls, value: str) -> Optional[dt.datetime]:
        if value:
            return parse_datestr(value)

    @field_validator("out_dir", "config_path")
    @classmethod
    def parse_str_to_path(cls, value: str) -> Optional[Path]:
        if value:
            return Path(value)
    model_config = ConfigDict(extra="allow", validate_default=True, arbitrary_types_allowed=True)
