from datetime import datetime
from typing import Union

from cg.constants import (
    Pipeline,
    NA_FIELD,
    YES_FIELD,
    NO_FIELD,
    PRECISION,
    REPORT_SUPPORTED_PIPELINES,
    BALSAMIC_ANALYSIS_TYPE,
)


def validate_empty_field(value: Union[int, str]) -> str:
    """Formats an empty value to be included in the report as 'N/A'"""

    return str(value) if value else NA_FIELD


def validate_boolean(value: Union[bool, str]) -> str:
    """Formats a boolean to include its value in the delivery report"""

    if isinstance(value, bool) or value:
        return YES_FIELD if str(value) == "True" else NO_FIELD

    return NA_FIELD


def validate_float(value: Union[float, str]) -> str:
    """Returns a processed float value"""

    return str(round(float(value), PRECISION)) if value else NA_FIELD


def validate_date(date: datetime) -> str:
    """Returns the date part (year, month, day) from a datetime object"""

    return str(date.date()) if date else NA_FIELD


def validate_list(value: list) -> str:
    """Formats a list elements as comma separated individual values"""

    return validate_empty_field(
        ", ".join(validate_empty_field(v) for v in value) if value else NA_FIELD
    )


def validate_rml_sample(prep_category: str) -> str:
    """Checks if a specific sample is a RML one"""

    if prep_category == "rml":
        raise ValueError("The delivery report generation does not support RML samples.")

    return validate_empty_field(prep_category)


def validate_balsamic_analysis_type(value: str) -> str:
    """Erases underscores from a string attribute"""

    return (
        BALSAMIC_ANALYSIS_TYPE.get(value)
        if value and BALSAMIC_ANALYSIS_TYPE.get(value)
        else NA_FIELD
    )


def validate_supported_pipeline(cls, values: dict) -> dict:
    """Validates if the report generation supports a specific pipeline and analysis type"""

    if values and values.get("pipeline") and values.get("customer_pipeline"):
        # Checks that the requested analysis and the executed one match
        if values.get("pipeline") != values.get("customer_pipeline"):
            raise ValueError(
                f"The analysis requested by the customer ({values.get('customer_pipeline')}) does not match the one "
                f"executed ({values.get('pipeline')})."
            )

        # Check that the generation of the report supports the data analysis executed on the case
        if values.get("pipeline") not in REPORT_SUPPORTED_PIPELINES:
            raise ValueError(
                f"The pipeline {values.get('pipeline')} does not support delivery report generation."
            )

    # Validates the analysis type
    if values.get("pipeline") == Pipeline.BALSAMIC:
        values["type"] = validate_balsamic_analysis_type(values["type"])

    return values
