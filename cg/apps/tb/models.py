import datetime as dt
from pathlib import Path
from typing import Optional

from dateutil.parser import parse as parse_datestr
from pydantic import field_validator, ConfigDict, BaseModel, validator


class TrailblazerAnalysis(BaseModel):
    id: int
    family: str
    case_id: Optional[str] = None

    version: Optional[str] = None
    logged_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    out_dir: Optional[str] = None
    config_path: Optional[str] = None
    comment: Optional[str] = None
    is_deleted: Optional[bool] = None
    is_visible: Optional[bool] = None
    type: Optional[str] = None
    user_id: Optional[int] = None
    progress: Optional[float] = 0.0
    data_analysis: Optional[str] = None
    ticket: Optional[str] = None
    uploaded_at: Optional[str] = None

    # TODO[pydantic]: We couldn't refactor the `validator`, please replace it by `field_validator` manually.
    # Check https://docs.pydantic.dev/dev-v2/migration/#changes-to-validators for more information.
    @field_validator("case_id")
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
