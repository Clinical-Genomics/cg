from typing import Optional

from pydantic import AfterValidator, BaseModel
from typing_extensions import Annotated

from cg.apps.tb.validators import inherit_family_value, parse_str_to_datetime, parse_str_to_path


class TrailblazerAnalysis(BaseModel):
    id: int
    family: str
    case_id: Annotated[Optional[str], AfterValidator(inherit_family_value)]

    version: Optional[str]
    logged_at: Annotated[Optional[str], AfterValidator(parse_str_to_datetime)]
    started_at: Annotated[Optional[str], AfterValidator(parse_str_to_datetime)]
    completed_at: Annotated[Optional[str], AfterValidator(parse_str_to_datetime)]
    status: Optional[str]
    priority: Optional[str]
    out_dir: Annotated[Optional[str], AfterValidator(parse_str_to_path)]
    config_path: Annotated[Optional[str], AfterValidator(parse_str_to_path)]
    comment: Optional[str]
    is_deleted: Optional[bool]
    is_visible: Optional[bool]
    type: Optional[str]
    user_id: Optional[int]
    progress: Optional[float] = 0.0
    data_analysis: Optional[str]
    ticket: Optional[str]
    uploaded_at: Optional[str]

    class Config:
        validate_default = True
        arbitrary_types_allowed = True
