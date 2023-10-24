import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from pydantic import ValidationInfo

from cg.constants import (
    BALSAMIC_ANALYSIS_TYPE,
    NA_FIELD,
    NO_FIELD,
    PRECISION,
    REPORT_GENDER,
    YES_FIELD,
)
from cg.constants.constants import Pipeline, PrepCategory
from cg.constants.subject import Gender
from cg.models.orders.constants import OrderType

LOG = logging.getLogger(__name__)


def get_report_string(value: Any) -> str:
    """Return report adapted string."""
    return str(value) if value else NA_FIELD


def get_boolean_as_string(value: Optional[bool]) -> str:
    """Return delivery report adapted string representation of a boolean."""
    if isinstance(value, bool):
        return YES_FIELD if value else NO_FIELD
    return NA_FIELD


def get_float_as_string(value: Optional[float]) -> str:
    """Return string representation of a float value."""
    return str(round(float(value), PRECISION)) if value or isinstance(value, float) else NA_FIELD


def get_float_as_percentage(value: Optional[float]) -> str:
    """Return string percentage representation of a float value."""
    return get_float_as_string(value * 100) if value or isinstance(value, float) else NA_FIELD


def get_date_as_string(date: Optional[datetime]) -> str:
    """Return the date string representation (year, month, day) of a datetime object."""
    return str(date.date()) if date else NA_FIELD


def get_list_as_string(value: Optional[list[str]]) -> str:
    """Return list elements as comma separated individual string values."""
    return ", ".join(v for v in value) if value else NA_FIELD


def get_path_as_string(file_path: Optional[str]) -> str:
    """Return a report validated file name."""
    return Path(file_path).name if file_path and Path(file_path).is_file() else NA_FIELD


def get_gender_as_string(gender: Optional[Gender]) -> str:
    """Return a report adapted gender."""
    return get_report_string(REPORT_GENDER.get(gender))


def get_prep_category_as_string(prep_category: Optional[PrepCategory]) -> str:
    """Return a report validated prep category as string."""
    if prep_category == OrderType.RML:
        LOG.error("The delivery report generation does not support RML samples")
        raise ValueError
    return get_report_string(prep_category)


def get_analysis_type_as_string(analysis_type: Optional[str], info: ValidationInfo) -> str:
    """Return the analysis type as an accepted string value for the delivery report."""
    if analysis_type and Pipeline.BALSAMIC in info.data.get("pipeline"):
        analysis_type: str = BALSAMIC_ANALYSIS_TYPE.get(analysis_type)
    return get_report_string(analysis_type)
