"""Report field validation helper"""

from typing import Optional

from cg.constants import NA_FIELD
from cg.constants.constants import SCALE_TO_MILLION_READ_PAIRS
from cg.models.report.report import ReportModel


def get_million_read_pairs(reads: int) -> Optional[float]:
    """Represents the number of sequencing reads as millions of read pairs."""
    return (
        round(reads / SCALE_TO_MILLION_READ_PAIRS, 1) if reads or isinstance(reads, int) else None
    )


def get_missing_fields(empty_fields: list, required_fields: list) -> list:
    """Extracts the missing fields that are required to generate successfully the delivery report."""
    missing_fields = list()
    for field in empty_fields:
        if field in required_fields:
            missing_fields.append(field)
    return missing_fields


def get_empty_fields(report_data: dict) -> list:
    """Returns a list of empty report fields."""
    empty_fields = list()
    for field, value in report_data.items():
        if not value or value == NA_FIELD:
            if isinstance(value, bool):
                continue
            empty_fields.append(field)
    return empty_fields


def get_empty_report_data(report_data: ReportModel) -> dict:
    """Retrieve empty fields from a report data model."""
    empty_fields = {
        "report": get_empty_fields(report_data=report_data.dict()),
        "customer": get_empty_fields(report_data=report_data.customer.dict()),
        "case": get_empty_fields(report_data=report_data.case.dict()),
        "applications": {
            app.tag: get_empty_fields(report_data=app.dict())
            for app in report_data.case.applications
            if get_empty_fields(report_data=app.dict())
        },
        "data_analysis": get_empty_fields(report_data=report_data.case.data_analysis.dict()),
        "samples": {
            sample.id: get_empty_fields(report_data=sample.dict())
            for sample in report_data.case.samples
            if get_empty_fields(report_data=sample.dict())
        },
        "methods": {
            sample.id: get_empty_fields(report_data=sample.methods.dict())
            for sample in report_data.case.samples
            if get_empty_fields(report_data=sample.methods.dict())
        },
        "timestamps": {
            sample.id: get_empty_fields(report_data=sample.timestamps.dict())
            for sample in report_data.case.samples
            if get_empty_fields(report_data=sample.timestamps.dict())
        },
        "metadata": {
            sample.id: get_empty_fields(report_data=sample.metadata.dict())
            for sample in report_data.case.samples
            if get_empty_fields(report_data=sample.metadata.dict())
        },
    }
    # Clear empty values
    empty_fields = {k: v for k, v in empty_fields.items() if v}
    return empty_fields


def get_missing_report_data(empty_fields: dict, required_fields: dict) -> dict:
    """Retrieve the missing required fields from a report data model."""
    nested_sources = ["applications", "samples", "methods", "timestamps", "metadata"]
    missing_fields = dict()
    for source in empty_fields:
        if source in nested_sources:
            # Associates application/sample tags/ids to missing fields
            missing_data = {
                tag: get_missing_fields(
                    empty_fields=empty_fields[source][tag],
                    required_fields=required_fields[source][tag],
                )
                for tag in empty_fields[source]
                if get_missing_fields(
                    empty_fields=empty_fields[source][tag],
                    required_fields=required_fields[source][tag],
                )
            }
        else:
            missing_data = get_missing_fields(
                empty_fields=empty_fields[source], required_fields=required_fields[source]
            )
        if missing_data:
            missing_fields.update({source: missing_data})
    return missing_fields
