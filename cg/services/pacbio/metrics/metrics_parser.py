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


class MetricsParser:
    """Class for parsing PacBio sequencing metrics."""

    def __init__(self, smrt_cell_path: Path) -> None:
        self.smrt_cell_path: Path = smrt_cell_path
        self.report_dir = Path(smrt_cell_path, "statistics")
        # For HiFi metrics
        self.base_calling_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.BASECALLING_REPORT
        )
        self.hifi_metrics: HiFiMetrics = self.parse_report_to_model(
            report_file=self.base_calling_report_file, data_model=HiFiMetrics
        )
        # For control metrics
        self.control_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        self.control_metrics: ControlMetrics = self.parse_report_to_model(
            report_file=self.control_report_file, data_model=ControlMetrics
        )
        # For productivity metrics
        self.loading_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        self.productivity_metrics: ProductivityMetrics = self.parse_report_to_model(
            report_file=self.loading_report_file, data_model=ProductivityMetrics
        )
        # For polymerase metrics
        self.raw_data_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )
        self.polymerase_metrics: PolymeraseMetrics = self.parse_report_to_model(
            report_file=self.raw_data_report_file, data_model=PolymeraseMetrics
        )
        # For SMRTlink datasets metrics
        self.smrtlink_datasets_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
        )
        self.smrtlink_datasets_metrics: SmrtlinkDatasetsMetrics = (
            self.parse_smrtlink_datasets_file()
        )

    @staticmethod
    def parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
        """Parse the metrics report to a data model."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
        metrics: list[dict[str, Any]] = parsed_json.get("attributes")
        data: dict = {report_field["id"]: report_field["value"] for report_field in metrics}
        return data_model.model_validate(data, from_attributes=True)

    def parse_smrtlink_datasets_file(self) -> SmrtlinkDatasetsMetrics:
        """Parse the SMRTlink datasets report file."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](self.smrtlink_datasets_report_file)
        data: dict = parsed_json[0]
        return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)
