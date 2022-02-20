from datetime import datetime
from typing import Union

from cg.constants import Pipeline
from cg.constants import REPORT_SUPPORTED_PIPELINES

PRECISION = 2
NA_FIELD = "N/A"
YES_FIELD = "Y"
NO_FIELD = "N"


def validate_empty_field(value: Union[int, str]) -> str:
    """Formats an empty value to be included in the report as 'N/A'"""

    return str(value) if value else NA_FIELD


def validate_boolean(value: Union[bool, str]) -> str:
    """Formats a boolean to include its value in the delivery report"""

    if value:
        return YES_FIELD if str(value) == "True" else NO_FIELD

    return NA_FIELD


def validate_float(value: Union[float, str]) -> str:
    """Returns a processed float value"""

    return str(round(float(value), PRECISION)) if value else NA_FIELD


def validate_date(date: datetime) -> str:
    """Return the date part (year, month, day) from a datetime object"""

    return str(date.date()) if date else NA_FIELD


def validate_list(value: list) -> list:
    """Formats a list elements as comma separated individual values"""

    return ", ".join(validate_empty_field(v) for v in value) if value else NA_FIELD


def validate_supported_pipeline(pipeline: Pipeline) -> Pipeline:
    """Validates if the report generation supports a specific pipeline"""

    if pipeline and pipeline not in REPORT_SUPPORTED_PIPELINES:
        raise ValueError(f"The pipeline {pipeline} does not support delivery report generation")

    return validate_empty_field(pipeline)


def validate_rml_sample(prep_category: str) -> str:
    """Checks if a specific sample is a RML one"""

    if prep_category == "rml":
        raise ValueError("The delivery report generation does not support RML samples")

    return validate_empty_field(prep_category)


def validate_processing_dates(cls, values: dict) -> dict:
    """Calculates the days it takes to deliver a sample and formats the sample processing timestamps"""

    if values.get("received_at") and values.get("delivered_at"):
        values["processing_days"] = validate_empty_field(
            (values.get("delivered_at") - values.get("received_at")).days
        )

    for k, v in values.items():
        if k != "processing_days":
            values[k] = validate_date(v)
        else:
            values[k] = validate_empty_field(v)

    return values
