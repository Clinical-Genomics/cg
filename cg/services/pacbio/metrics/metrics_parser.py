from pathlib import Path
from typing import Any, Type

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.io.controller import ReadFile
from cg.services.pacbio.metrics.models import ControlMetrics, HiFiMetrics, ProductivityMetrics
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
        self.hifi_metrics: HiFiMetrics = self.parse_attributes_to_model(
            report_file=self.base_calling_report_file, data_model=HiFiMetrics
        )
        # For control metrics
        self.control_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        self.control_metrics: ControlMetrics = self.parse_attributes_to_model(
            report_file=self.control_report_file, data_model=ControlMetrics
        )
        # For productivity metrics
        self.loading_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        self.productivity_metrics: ProductivityMetrics = self.parse_attributes_to_model(
            report_file=self.loading_report_file, data_model=ProductivityMetrics
        )
        # For polymerase metrics
        self.raw_data_report_file: Path = get_file_in_directory(
            directory=self.report_dir, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )

    @staticmethod
    def _parse_report(report_file: Path) -> list[dict[str, Any]]:
        """Parse the attribute element of a PacBio report file in JSON format."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
        return parsed_json.get("attributes")

    def parse_attributes_to_model(
        self,
        report_file: Path,
        data_model: Type[ControlMetrics | HiFiMetrics | ProductivityMetrics],
    ) -> ControlMetrics | HiFiMetrics | ProductivityMetrics:
        """Parse the attributes to a model."""
        report_content: list[dict[str, Any]] = self._parse_report(report_file=report_file)
        data: dict = {report_field["id"]: report_field["value"] for report_field in report_content}
        return data_model.model_validate(data, from_attributes=True)
