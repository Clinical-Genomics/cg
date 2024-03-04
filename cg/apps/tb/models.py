import datetime as dt
from pathlib import Path

from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing_extensions import Annotated

from cg.apps.tb.validators import parse_str_to_datetime, parse_str_to_path


class TrailblazerAnalysis(BaseModel):
    id: int
    case_id: str | None = None
    version: str | None = None
    logged_at: Annotated[dt.datetime | None, BeforeValidator(parse_str_to_datetime)]
    started_at: Annotated[dt.datetime | None, BeforeValidator(parse_str_to_datetime)]
    completed_at: Annotated[dt.datetime | None, BeforeValidator(parse_str_to_datetime)]
    status: str | None = None
    priority: str | None = None
    out_dir: Annotated[Path | None, BeforeValidator(parse_str_to_path)]
    config_path: Annotated[Path | None, BeforeValidator(parse_str_to_path)]
    comment: str | None = None
    is_deleted: bool | None = None
    is_visible: bool | None = None
    type: str | None = None
    user_id: int | None = None
    progress: float | None = 0.0
    workflow: str | None = None
    ticket: str | None = None
    uploaded_at: str | None = None

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_default=True,
        extra="ignore",
    )


class AnalysesResponse(BaseModel):
    analyses: list[TrailblazerAnalysis]
