from pathlib import Path
from typing import Any, Type

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.io.controller import ReadFile
from cg.services.pacbio.metrics.models import (
    BaseMetrics,
    ControlMetrics,
    HiFiMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.utils.files import get_file_in_directory


def parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
    """Parse the metrics report to a data model."""
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
    metrics: list[dict[str, Any]] = parsed_json.get("attributes")
    data: dict = {report_field["id"]: report_field["value"] for report_field in metrics}
    return data_model.model_validate(data, from_attributes=True)


def parse_dataset_metrics(report_dir: Path) -> SmrtlinkDatasetsMetrics:
    file_name = PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
    report: Path = get_file_in_directory(directory=report_dir, file_name=file_name)
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](report)
    data: dict = parsed_json[0]
    return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)


def parse_hifi_metrics(report_dir: Path) -> HiFiMetrics:
    file_name = PacBioDirsAndFiles.BASECALLING_REPORT
    report: Path = get_file_in_directory(directory=report_dir, file_name=file_name)
    return parse_report_to_model(report_file=report, data_model=HiFiMetrics)


def parse_control_metrics(report_dir: Path) -> ControlMetrics:
    file_name = PacBioDirsAndFiles.CONTROL_REPORT
    report: Path = get_file_in_directory(directory=report_dir, file_name=file_name)
    return parse_report_to_model(report_file=report, data_model=ControlMetrics)


def parse_productivity_metrics(report_dir: Path) -> ProductivityMetrics:
    file_name = PacBioDirsAndFiles.LOADING_REPORT
    report: Path = get_file_in_directory(directory=report_dir, file_name=file_name)
    return parse_report_to_model(report_file=report, data_model=ProductivityMetrics)


def parse_polymerase_metrics(report_dir: Path) -> PolymeraseMetrics:
    file_name = PacBioDirsAndFiles.RAW_DATA_REPORT
    report: Path = get_file_in_directory(directory=report_dir, file_name=file_name)
    return parse_report_to_model(report_file=report, data_model=PolymeraseMetrics)
