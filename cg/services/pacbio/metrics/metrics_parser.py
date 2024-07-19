from pathlib import Path
from typing import Any, Type

from cg.constants.constants import FileFormat
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.io.controller import ReadFile
from cg.services.pacbio.metrics.models import (
    BaseMetrics,
    ControlMetrics,
    HiFiMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.utils.files import get_file_in_directory


class PacBioMetricsParser:
    """Class for parsing PacBio sequencing metrics."""

    def __init__(self) -> None:
        self.base_calling_report_file: Path | None = None
        self.control_report_file: Path | None = None
        self.loading_report_file: Path | None = None
        self.raw_data_report_file: Path | None = None
        self.smrtlink_datasets_report_file: Path | None = None

    def _set_report_paths(self, smrt_cell_path: Path) -> None:
        """Set the paths for all the sequencing reports."""
        report_dir = Path(smrt_cell_path, "statistics")
        self.base_calling_report_file: Path = get_file_in_directory(
            directory=report_dir, file_name=PacBioDirsAndFiles.BASECALLING_REPORT
        )
        self.control_report_file: Path = get_file_in_directory(
            directory=report_dir, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        self.loading_report_file: Path = get_file_in_directory(
            directory=report_dir, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        self.raw_data_report_file: Path = get_file_in_directory(
            directory=report_dir, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )
        self.smrtlink_datasets_report_file: Path = get_file_in_directory(
            directory=report_dir, file_name=PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
        )

    @staticmethod
    def _parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
        """Parse the metrics report to a data model."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
        metrics: list[dict[str, Any]] = parsed_json.get("attributes")
        data: dict = {report_field["id"]: report_field["value"] for report_field in metrics}
        return data_model.model_validate(data, from_attributes=True)

    def _parse_smrtlink_datasets_file(self) -> SmrtlinkDatasetsMetrics:
        """Parse the SMRTlink datasets report file."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](self.smrtlink_datasets_report_file)
        data: dict = parsed_json[0]
        return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)

    def _get_hifi_metrics(self) -> HiFiMetrics:
        """Return the parsed Hi-Fi metrics in a metrics Pydantic object."""
        return self._parse_report_to_model(
            report_file=self.base_calling_report_file, data_model=HiFiMetrics
        )

    def _get_control_metrics(self) -> ControlMetrics:
        """Return the parsed Control metrics in a metrics Pydantic object."""
        return self._parse_report_to_model(
            report_file=self.control_report_file, data_model=ControlMetrics
        )

    def _get_productivity_metrics(self) -> ProductivityMetrics:
        """Return the parsed Productivity metrics in a metrics Pydantic object."""
        return self._parse_report_to_model(
            report_file=self.loading_report_file, data_model=ProductivityMetrics
        )

    def _get_polymerase_metrics(self) -> PolymeraseMetrics:
        """Return the parsed Polymerase metrics in a metrics Pydantic object."""
        return self._parse_report_to_model(
            report_file=self.raw_data_report_file, data_model=PolymeraseMetrics
        )

    def _get_smrtlink_datasets_metrics(self) -> SmrtlinkDatasetsMetrics:
        """Return the parsed SMRTlink datasets metrics in a metrics Pydantic object."""
        return self._parse_smrtlink_datasets_file()

    def parse_metrics(self, smrt_cell_path: Path) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        self._set_report_paths(smrt_cell_path)
        hifi_metrics: HiFiMetrics = self._get_hifi_metrics()
        control_metrics: ControlMetrics = self._get_control_metrics()
        productivity_metrics: ProductivityMetrics = self._get_productivity_metrics()
        polymerase_metrics: PolymeraseMetrics = self._get_polymerase_metrics()
        smrtlink_datasets_metrics: SmrtlinkDatasetsMetrics = self._get_smrtlink_datasets_metrics()
        return PacBioMetrics(
            device_internal_id=smrtlink_datasets_metrics.cell_id,
            well=smrtlink_datasets_metrics.well,
            well_sample_name=smrtlink_datasets_metrics.well_sample_name,
            sample_internal_id=smrtlink_datasets_metrics.sample_internal_id,
            movie_name=smrtlink_datasets_metrics.movie_name,
            cell_index=smrtlink_datasets_metrics.cell_index,
            plate=smrtlink_datasets_metrics.plate,
            hifi_reads=hifi_metrics.reads,
            hifi_yield=hifi_metrics.yield_,
            hifi_mean_read_length=hifi_metrics.mean_read_length_kb,
            hifi_median_read_length=hifi_metrics.median_read_length,
            hifi_mean_length_n50=hifi_metrics.mean_length_n50,
            hifi_median_read_quality=hifi_metrics.median_read_quality,
            percent_q30=hifi_metrics.percent_q30,
            control_reads=control_metrics.reads,
            control_mean_read_length=control_metrics.mean_read_length_kb,
            control_mean_concordance_reads=control_metrics.percent_mean_concordance_reads,
            control_mode_concordance_reads=control_metrics.percent_mode_concordance_reads,
            productive_zmws=productivity_metrics.productive_zmws,
            p_0=productivity_metrics.p_0,
            p_1=productivity_metrics.p_1,
            p_2=productivity_metrics.p_2,
            percent_p_0=productivity_metrics.percent_p_0,
            percent_p_1=productivity_metrics.percent_p_1,
            percent_p_2=productivity_metrics.percent_p_2,
            polymerase_mean_read_length=polymerase_metrics.mean_read_length,
            polymerase_read_length_n50=polymerase_metrics.read_length_n50,
            polymerase_mean_longest_subread_length=polymerase_metrics.mean_longest_subread_length,
            polymerase_longest_subread_length_n50=polymerase_metrics.longest_subread_length_n50,
        )
