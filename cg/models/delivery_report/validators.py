import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationInfo

from cg.constants import (
    BALSAMIC_ANALYSIS_TYPE,
    NA_FIELD,
    NO_FIELD,
    PRECISION,
    REPORT_SEX,
    YES_FIELD,
)
from cg.constants.constants import Workflow
from cg.constants.report import REPORT_QC_FLAG
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.constants.subject import Sex
from cg.models.delivery.delivery import DeliveryFile
from cg.models.orders.constants import OrderType

LOG = logging.getLogger(__name__)


def get_report_string(value: Any) -> str:
    """Return report adapted string."""
    return str(value) if value else NA_FIELD


def get_boolean_as_string(value: bool | None) -> str:
    """Return delivery report adapted string representation of a boolean."""
    if isinstance(value, bool):
        return YES_FIELD if value else NO_FIELD
    return NA_FIELD


def get_number_as_string(value: Any) -> str:
    """
    Return string representation of a number. If None is provided, then it returns N/A.

    Raises:
        ValueError: If the input value cannot be converted to a float.
    """
    try:
        result: str = str(round(float(value), PRECISION))
        return result
    except TypeError:
        return NA_FIELD
    except ValueError:
        LOG.error(f"Value {value} cannot be converted to float")
        raise


def get_float_as_percentage(value: float | None) -> str:
    """Return string percentage representation of a float value."""
    return get_number_as_string(value * 100) if value or isinstance(value, float) else NA_FIELD


def get_date_as_string(date: datetime | None) -> str:
    """Return the date string representation (year, month, day) of a datetime object."""
    return str(date.date()) if date else NA_FIELD


def get_list_as_string(value: list[str] | None) -> str:
    """Return list elements as comma separated individual string values."""
    return ", ".join(v for v in value) if value else NA_FIELD


def get_delivered_files_as_file_names(delivery_files: list[DeliveryFile] | None) -> list[str] | str:
    """Return a list of validated file names given a list of delivery files."""
    return [file.destination_path.name for file in delivery_files] if delivery_files else NA_FIELD


def get_path_as_string(file_path: str | None) -> str:
    """Return a report validated file name."""
    return Path(file_path).name if file_path and Path(file_path).is_file() else NA_FIELD


def get_sex_as_string(sex: Sex | None) -> str:
    """Return a report adapted sex."""
    return get_report_string(REPORT_SEX.get(sex))


def get_prep_category_as_string(prep_category: SeqLibraryPrepCategory | None) -> str:
    """Return a report validated prep category as string."""
    if prep_category == OrderType.RML:
        LOG.error("The delivery report generation does not support RML samples")
        raise ValueError
    return get_report_string(prep_category)


def get_analysis_type_as_string(analysis_type: str | None, info: ValidationInfo) -> str:
    """Return the analysis type as an accepted string value for the delivery report."""
    if analysis_type and Workflow.BALSAMIC in info.data.get("workflow"):
        analysis_type: str = BALSAMIC_ANALYSIS_TYPE.get(analysis_type)
    return get_report_string(analysis_type)


def get_initial_qc_as_string(qc_flag: bool | None) -> str:
    """Return a report adapted initial quality control flag."""
    return get_report_string(REPORT_QC_FLAG.get(qc_flag))
