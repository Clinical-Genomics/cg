from pathlib import Path
from typing import Any, Type

from cg.constants.constants import FileFormat
from cg.constants.pacbio import MetricsFileFields, PacBioDirsAndFiles
from cg.io.controller import ReadFile
from cg.services.run_devices.pacbio.metrics_parser.models import (
    BarcodeMetrics,
    BaseMetrics,
    ControlMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    ReadMetrics,
    SampleMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.utils.files import get_file_with_pattern_from_list


def _get_data_model_from_pattern(pattern: str) -> Type[BaseMetrics]:
    """Return the data model based on the pattern."""
    pattern_to_model = {
        PacBioDirsAndFiles.BARCODES_REPORT: BarcodeMetrics,
        PacBioDirsAndFiles.CCS_REPORT_SUFFIX: ReadMetrics,
        PacBioDirsAndFiles.CONTROL_REPORT: ControlMetrics,
        PacBioDirsAndFiles.LOADING_REPORT: ProductivityMetrics,
        PacBioDirsAndFiles.RAW_DATA_REPORT: PolymeraseMetrics,
        PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT: SmrtlinkDatasetsMetrics,
    }
    return pattern_to_model.get(pattern)


def _parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
    """Parse the metrics report to a data model."""
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](report_file)
    if data_model == SmrtlinkDatasetsMetrics:
        return data_model.model_validate(parsed_json[0])
    metrics: list[dict[str, Any]] = parsed_json.get(MetricsFileFields.ATTRIBUTES)
    data: dict = {
        report_field[MetricsFileFields.ID]: report_field[MetricsFileFields.VALUE]
        for report_field in metrics
    }
    return data_model.model_validate(data)


def get_parsed_metrics_from_file_name(metrics_files: list[Path], file_name: str) -> BaseMetrics:
    report_file: Path = get_file_with_pattern_from_list(files=metrics_files, pattern=file_name)
    data_model: Type[BaseMetrics] = _get_data_model_from_pattern(pattern=file_name)
    return _parse_report_to_model(report_file=report_file, data_model=data_model)


def _is_unassigned_reads_entry(sample_metric: SampleMetrics) -> bool:
    return sample_metric.sample_internal_id == "No Name"


def _parse_sample_data(sample_data: list[dict[str, Any]]) -> list[SampleMetrics]:
    """Parse all samples data into SampleMetrics given the sample section of the barcodes report."""
    sample_metrics: list[SampleMetrics] = []
    number_of_samples: int = len(sample_data[0].get(MetricsFileFields.VALUES))
    for sample_idx in range(number_of_samples):
        sample: dict = {}
        for data_field in sample_data:
            field_id: str = data_field.get(MetricsFileFields.ID)
            sample[field_id] = data_field.get(MetricsFileFields.VALUES)[sample_idx]
        sample_metric = SampleMetrics.model_validate(sample)
        if not _is_unassigned_reads_entry(sample_metric):
            sample_metrics.append(sample_metric)
    return sample_metrics


def get_parsed_sample_metrics(metrics_files: list[Path]) -> list[SampleMetrics]:
    """Parse the metrics from the barcodes report for each sample."""
    report_file: Path = get_file_with_pattern_from_list(
        files=metrics_files, pattern=PacBioDirsAndFiles.BARCODES_REPORT
    )
    parsed_json: dict = ReadFile.read_file[FileFormat.JSON](report_file)
    sample_data: list[dict[str, Any]] = parsed_json.get(MetricsFileFields.TABLES)[0].get(
        MetricsFileFields.COLUMNS
    )
    return _parse_sample_data(sample_data)
