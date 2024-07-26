from pathlib import Path

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.post_processing.abstract_classes import PostProcessingMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import (
    ControlMetrics,
    HiFiMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.services.post_processing.pacbio.metrics_parser.utils import (
    get_parsed_metrics_from_file_name,
)
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


class PacBioMetricsParser(PostProcessingMetricsParser):
    """Class for parsing PacBio sequencing metrics."""

    def __init__(self, file_manager: PacBioRunFileManager):
        super().__init__(file_manager=file_manager)

    def parse_metrics(self, run_data: PacBioRunData) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        metrics_files: list[Path] = self.file_manager.get_files_to_parse(run_data)
        hifi_metrics: HiFiMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.BASECALLING_REPORT
        )
        control_metrics: ControlMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.CONTROL_REPORT
        )
        productivity_metrics: ProductivityMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.LOADING_REPORT
        )
        polymerase_metrics: PolymeraseMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.RAW_DATA_REPORT
        )
        dataset_metrics: SmrtlinkDatasetsMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT
        )

        return PacBioMetrics(
            hifi=hifi_metrics,
            control=control_metrics,
            productivity=productivity_metrics,
            polymerase=polymerase_metrics,
            dataset_metrics=dataset_metrics,
        )
