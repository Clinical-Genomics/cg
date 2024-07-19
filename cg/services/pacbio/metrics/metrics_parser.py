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

    @staticmethod
    def _parse_report_to_model(report_file: Path, data_model: Type[BaseMetrics]) -> BaseMetrics:
        """Parse the metrics report to a data model."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](file_path=report_file)
        metrics: list[dict[str, Any]] = parsed_json.get("attributes")
        data: dict = {report_field["id"]: report_field["value"] for report_field in metrics}
        return data_model.model_validate(data, from_attributes=True)

    @staticmethod
    def _parse_smrtlink_datasets_file(
        smrtlink_datasets_report_file: Path,
    ) -> SmrtlinkDatasetsMetrics:
        """Parse the SMRTlink datasets report file."""
        parsed_json: dict = ReadFile.read_file[FileFormat.JSON](smrtlink_datasets_report_file)
        data: dict = parsed_json[0]
        return SmrtlinkDatasetsMetrics.model_validate(data, from_attributes=True)

    def _get_hifi_metrics(self, reports_dir: Path) -> HiFiMetrics:
        """Return the parsed Hi-Fi metrics in a metrics Pydantic object."""
        base_calling_report_file: Path = get_file_in_directory(
            directory=reports_dir, file_name=PacBioDirsAndFiles.BASECALLING_REPORT
        )
        return self._parse_report_to_model(
            report_file=base_calling_report_file, data_model=HiFiMetrics
        )

    def _get_control_metrics(self, reports_dir: Path) -> ControlMetrics:
        """Return the parsed Control metrics in a metrics Pydantic object."""
        control_report_file: Path = get_file_in_directory(
            directory=reports_dir, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        return self._parse_report_to_model(
            report_file=control_report_file, data_model=ControlMetrics
        )

    def _get_productivity_metrics(self, reports_dir: Path) -> ProductivityMetrics:
        """Return the parsed Productivity metrics in a metrics Pydantic object."""
        loading_report_file: Path = get_file_in_directory(
            directory=reports_dir, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        return self._parse_report_to_model(
            report_file=loading_report_file, data_model=ProductivityMetrics
        )

    def _get_polymerase_metrics(self, reports_dir: Path) -> PolymeraseMetrics:
        """Return the parsed Polymerase metrics in a metrics Pydantic object."""
        raw_data_report_file: Path = get_file_in_directory(
            directory=reports_dir, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )
        return self._parse_report_to_model(
            report_file=raw_data_report_file, data_model=PolymeraseMetrics
        )

    def _get_smrtlink_datasets_metrics(self, reports_dir: Path) -> SmrtlinkDatasetsMetrics:
        """Return the parsed SMRTlink datasets metrics in a metrics Pydantic object."""
        smrtlink_datasets_report_file: Path = get_file_in_directory(
            directory=reports_dir, file_name=PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
        )
        return self._parse_smrtlink_datasets_file(smrtlink_datasets_report_file)

    def parse_metrics(self, smrt_cell_path: Path) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        reports_dir = Path(smrt_cell_path, "statistics")
        hifi_metrics: HiFiMetrics = self._get_hifi_metrics(reports_dir)
        control_metrics: ControlMetrics = self._get_control_metrics(reports_dir)
        productivity_metrics: ProductivityMetrics = self._get_productivity_metrics(reports_dir)
        polymerase_metrics: PolymeraseMetrics = self._get_polymerase_metrics(reports_dir)
        smrtlink_datasets_metrics: SmrtlinkDatasetsMetrics = self._get_smrtlink_datasets_metrics(
            reports_dir
        )
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
