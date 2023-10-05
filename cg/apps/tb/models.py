import datetime as dt
from pathlib import Path
from typing import Optional

from pydantic import (
    BaseModel,
    BeforeValidator,
    ConfigDict,
    FieldValidationInfo,
    field_validator,
)
from typing_extensions import Annotated

from cg.apps.tb.validators import parse_str_to_datetime, parse_str_to_path


class TrailblazerAnalysis(BaseModel):
    id: int
    family: str
    case_id: Optional[str] = None

    @field_validator("case_id")
    @classmethod
    def inherit_family_value(cls, value: str, info: FieldValidationInfo) -> str:
        return info.data.get("family")

    version: Optional[str] = None
    logged_at: Annotated[Optional[dt.datetime], BeforeValidator(parse_str_to_datetime)]
    started_at: Annotated[Optional[dt.datetime], BeforeValidator(parse_str_to_datetime)]
    completed_at: Annotated[Optional[dt.datetime], BeforeValidator(parse_str_to_datetime)]
    status: Optional[str] = None
    priority: Optional[str] = None
    out_dir: Annotated[Optional[Path], BeforeValidator(parse_str_to_path)]
    config_path: Annotated[Optional[Path], BeforeValidator(parse_str_to_path)]
    comment: Optional[str] = None
    is_deleted: Optional[bool] = None
    is_visible: Optional[bool] = None
    type: Optional[str] = None
    user_id: Optional[int] = None
    progress: Optional[float] = 0.0
    data_analysis: Optional[str] = None
    ticket: Optional[str] = None
    uploaded_at: Optional[str] = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        extra="ignore",
    )
