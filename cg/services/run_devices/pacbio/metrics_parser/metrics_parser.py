from pathlib import Path

from pydantic import ValidationError

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.abstract_classes import PostProcessingMetricsParser
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import (
    PostProcessingParsingError,
    PostProcessingRunFileManagerError,
)
from cg.services.run_devices.pacbio.metrics_parser.models import (
    ControlMetrics,
    PacBioMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    ReadMetrics,
    SmrtlinkDatasetsMetrics,
)
from cg.services.run_devices.pacbio.metrics_parser.utils import (
    get_parsed_metrics_from_file_name,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


class PacBioMetricsParser(PostProcessingMetricsParser):
    """Class for parsing PacBio sequencing metrics."""

    def __init__(self, file_manager: PacBioRunFileManager):
        self.file_manager: PacBioRunFileManager = file_manager

    @handle_post_processing_errors(
        to_except=(FileNotFoundError, ValidationError, PostProcessingRunFileManagerError),
        to_raise=PostProcessingParsingError,
    )
    def parse_metrics(self, run_data: PacBioRunData) -> PacBioMetrics:
        """Return all the relevant PacBio metrics parsed in a single Pydantic object."""
        metrics_files: list[Path] = self.file_manager.get_files_to_parse(run_data)
        read_metrics: ReadMetrics = get_parsed_metrics_from_file_name(
            metrics_files=metrics_files, file_name=PacBioDirsAndFiles.CCS_REPORT_SUFFIX
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
            read=read_metrics,
            control=control_metrics,
            productivity=productivity_metrics,
            polymerase=polymerase_metrics,
            dataset_metrics=dataset_metrics,
        )
