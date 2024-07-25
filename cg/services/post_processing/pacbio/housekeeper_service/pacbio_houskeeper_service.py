"""Module for the PacBioHousekeeperService used in the Post processing flow."""

from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.pacbio.metrics.metrics_parser import PacBioMetricsParser
from cg.services.pacbio.metrics.models import PacBioMetrics
from cg.services.post_processing.abstract_classes import PostProcessingHKService
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)


class PacBioHousekeeperService(PostProcessingHKService):

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        file_manager: PacBioRunFileManager,
        metrics_parser: PacBioMetricsParser,
    ):
        super().__init__(hk_api=hk_api, file_manager=file_manager, metrics_parser=metrics_parser)

    def store_files_in_housekeeper(self, run_data: PacBioRunData):
        parsed_metrics: PacBioMetrics = self.metrics_parser.parse_metrics(
            self.file_manager.get_files_to_parse(run_data)
        )
        file_to_store: list[Path] = self.file_manager.get_files_to_store(run_data)
