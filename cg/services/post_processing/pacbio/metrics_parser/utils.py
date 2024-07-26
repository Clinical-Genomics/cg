from functools import wraps
from pathlib import Path
from typing import Any, Type

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.exc import PacBioMetricsParsingError
from cg.io.controller import ReadFile
from cg.services.post_processing.pacbio.metrics_parser.models import (
    BaseMetrics,
    ControlMetrics,
    HiFiMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)


def handle_pac_bio_parsing_errors(func):
    """Decorator to catch any metrics parsing error to raise a PacBioMetricsParsingError instead."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except FileNotFoundError as error:
            raise PacBioMetricsParsingError(f"Could not find the metrics file: {error}")
        except Exception as error:
            raise PacBioMetricsParsingError(f"An error occurred while parsing the metrics: {error}")

    return wrapper


def get_report_file_from_pattern(files: list[Path], pattern: str) -> Path | None:
    """
    Return the path whose name matches a pattern from a list of paths.
    Raises:
        FileNotFoundError: If no file matches the pattern.
    """
    for file in files:
        if pattern in file.name:
            return file
    raise FileNotFoundError(f"No {pattern} file found in given file list")


@handle_pac_bio_parsing_errors
def parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
    """Parse the metrics report to a data model."""
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
    metrics: list[dict[str, Any]] = parsed_json.get("attributes")
    data: dict = {report_field["id"]: report_field["value"] for report_field in metrics}
    return data_model.model_validate(data, from_attributes=True)


@handle_pac_bio_parsing_errors
def parse_dataset_metrics(metrics_files: list[Path]) -> SmrtlinkDatasetsMetrics:
    report_file: Path = get_report_file_from_pattern(
        files=metrics_files, pattern=PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
    )
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](report_file)
    data: dict = parsed_json[0]
    return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)


@handle_pac_bio_parsing_errors
def parse_hifi_metrics(metrics_files: list[Path]) -> HiFiMetrics:
    report_file: Path = get_report_file_from_pattern(
        files=metrics_files, pattern=PacBioDirsAndFiles.BASECALLING_REPORT
    )
    return parse_report_to_model(report_file=report_file, data_model=HiFiMetrics)


@handle_pac_bio_parsing_errors
def parse_control_metrics(metrics_files: list[Path]) -> ControlMetrics:
    report_file: Path = get_report_file_from_pattern(
        files=metrics_files, pattern=PacBioDirsAndFiles.CONTROL_REPORT
    )
    return parse_report_to_model(report_file=report_file, data_model=ControlMetrics)


@handle_pac_bio_parsing_errors
def parse_productivity_metrics(metrics_files: list[Path]) -> ProductivityMetrics:
    report_file: Path = get_report_file_from_pattern(
        files=metrics_files, pattern=PacBioDirsAndFiles.LOADING_REPORT
    )
    return parse_report_to_model(report_file=report_file, data_model=ProductivityMetrics)


@handle_pac_bio_parsing_errors
def parse_polymerase_metrics(metrics_files: list[Path]) -> PolymeraseMetrics:
    report_file: Path = get_report_file_from_pattern(
        files=metrics_files, pattern=PacBioDirsAndFiles.RAW_DATA_REPORT
    )
    return parse_report_to_model(report_file=report_file, data_model=PolymeraseMetrics)
