from pathlib import Path
from typing import Any, Callable

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.io.controller import ReadFile
from cg.services.pacbio_services.pacbio_metrics_service.models import HiFiMetrics
from cg.utils.files import get_file_in_directory


class MetricsParser:
    """Class for parsing PacBio sequencing metrics."""

    def __init__(self, smrt_cell_path: Path) -> None:
        self.smrt_cell_path: Path = smrt_cell_path
        self.report_path = Path(smrt_cell_path, "statistics")
        # For HiFi metrics
        self.css_report_path: Path = get_file_in_directory(
            directory=self.report_path, file_name=PacBioDirsAndFiles.CSS_REPORT
        )
        # For control metrics
        self.control_report_path: Path = get_file_in_directory(
            directory=self.report_path, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        # For productivity metrics
        self.loading_report_path: Path = get_file_in_directory(
            directory=self.report_path, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        # For polymerase metrics
        self.raw_data_report_path: Path = get_file_in_directory(
            directory=self.report_path, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )
        self.hifi_metrics: HiFiMetrics = self.parse_attributes_to_model(
            json_file=self.css_report_path, model=HiFiMetrics
        )

    def _parse_attributes_from_json(self, json_file: Path) -> list[dict[str, Any]]:
        """Parse the attribute element of a PacBio JSON file."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=json_file)
        return parsed_json.get("attributes")

    def parse_attributes_to_model(self, json_file: Path, model: Callable) -> HiFiMetrics:
        """Parse the attributes to a model."""
        attributes: list[dict[str, Any]] = self._parse_attributes_from_json(json_file=json_file)
        data: dict = {attr["id"]: attr["value"] for attr in attributes}
        return model(**data)
