import logging
from datetime import datetime
from pathlib import Path
from typing import Union

from cg.models.orders.constants import OrderType
from cg.constants import (
    Pipeline,
    NA_FIELD,
    YES_FIELD,
    NO_FIELD,
    PRECISION,
    REPORT_SUPPORTED_PIPELINES,
    BALSAMIC_ANALYSIS_TYPE,
    REPORT_GENDER,
)

LOG = logging.getLogger(__name__)


def validate_empty_field(value: Union[int, str]) -> str:
    """Formats an empty value to be included in the report as N/A."""
    return str(value) if value else NA_FIELD


def validate_boolean(value: Union[bool, str]) -> str:
    """Formats a boolean value for the delivery report."""
    if isinstance(value, bool) or value:
        if str(value) == "True":
            return YES_FIELD
        if str(value) == "False":
            return NO_FIELD
    return NA_FIELD


def validate_float(value: Union[float, str]) -> str:
    """Returns a processed float value."""
    return str(round(float(value), PRECISION)) if value or isinstance(value, float) else NA_FIELD


def validate_percentage(value: Union[float, str]) -> str:
    """Returns a processed float value as a percentage."""
    return validate_float(float(value) * 100) if value else NA_FIELD


def validate_date(date: datetime) -> str:
    """Returns the date part (year, month, day) from a datetime object."""
    return str(date.date()) if date else NA_FIELD


def validate_list(value: list) -> str:
    """Formats a list elements as comma separated individual values."""
    return validate_empty_field(
        ", ".join(validate_empty_field(v) for v in value) if value else NA_FIELD
    )


def validate_path(file_path: str) -> str:
    """Returns the name of a specific file."""
    return Path(file_path).name if file_path and Path(file_path).is_file() else NA_FIELD


def validate_gender(value: str) -> str:
    """Formats the provided gender."""
    return validate_empty_field(REPORT_GENDER.get(value))


def validate_rml_sample(prep_category: str) -> str:
    """Checks if a specific sample is a RML one."""
    if prep_category == OrderType.RML:
        LOG.error("The delivery report generation does not support RML samples")
        raise ValueError
    return validate_empty_field(prep_category)


def validate_balsamic_analysis_type(value: str) -> str:
    """Translates the BALSAMIC analysis type string to an accepted value for the delivery report."""
    return validate_empty_field(BALSAMIC_ANALYSIS_TYPE.get(value))


def validate_supported_pipeline(cls, values: dict) -> dict:
    """Validates if the report generation supports a specific pipeline and analysis type."""
    if values and values.get("pipeline") and values.get("customer_pipeline"):
        # Checks that the requested analysis and the executed one match
        if values.get("pipeline") != values.get("customer_pipeline"):
            LOG.error(
                f"The analysis requested by the customer ({values.get('customer_pipeline')}) does not match the one "
                f"executed ({values.get('pipeline')})"
            )
            raise ValueError
        # Check that the generation of the report supports the data analysis executed on the case
        if values.get("pipeline") not in REPORT_SUPPORTED_PIPELINES:
            LOG.error(
                f"The pipeline {values.get('pipeline')} does not support delivery report generation"
            )
            raise ValueError
    # Validates the analysis type
    if Pipeline.BALSAMIC in values.get("pipeline"):
        values["type"] = validate_balsamic_analysis_type(values["type"])
    return values
