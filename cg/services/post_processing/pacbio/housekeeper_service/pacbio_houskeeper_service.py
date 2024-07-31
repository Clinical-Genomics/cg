"""Module for the PacBioHousekeeperService used in the Post processing flow."""

from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.pacbio import PacBioBundleTypes, file_pattern_to_bundle_type, file_pattern_to_tag
from cg.services.post_processing.abstract_classes import PostProcessingHKService
from cg.services.post_processing.pacbio.housekeeper_service.models import PacBioFileData
from cg.services.post_processing.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.pacbio.run_file_manager.run_file_manager import (
    PacBioRunFileManager,
)
from cg.utils.mapping import get_item_by_pattern_in_source


class PacBioHousekeeperService(PostProcessingHKService):

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        file_manager: PacBioRunFileManager,
        metrics_parser: PacBioMetricsParser,
    ):
        self.hk_api: HousekeeperAPI = hk_api
        self.file_manager: PacBioRunFileManager = file_manager
        self.metrics_parser: PacBioMetricsParser = metrics_parser

    def store_files_in_housekeeper(self, run_data: PacBioRunData):
        parsed_metrics: PacBioMetrics = self.metrics_parser.parse_metrics(run_data)
        file_to_store: list[Path] = self.file_manager.get_files_to_store(run_data)
        for file_path in file_to_store:
            bundle_info: PacBioFileData = self._create_bundle_info(
                file_path=file_path, parsed_metrics=parsed_metrics
            )
            self.hk_api.create_bundle_and_add_file_with_tags(
                bundle_name=bundle_info.bundle_name,
                file_path=bundle_info.file_path,
                tags=bundle_info.tags,
            )

    @staticmethod
    def _get_bundle_type_for_file(file_path: Path) -> str:
        return get_item_by_pattern_in_source(
            source=file_path.name, pattern_map=file_pattern_to_bundle_type
        )

    @staticmethod
    def _get_tags_for_file(file_path: Path) -> list[str]:
        return get_item_by_pattern_in_source(source=file_path.name, pattern_map=file_pattern_to_tag)

    def _create_bundle_info(self, file_path: Path, parsed_metrics: PacBioMetrics) -> PacBioFileData:
        tags: list[str] = self._get_tags_for_file(file_path)
        if self._is_file_type_smrt_cell(file_path):
            tags.append(parsed_metrics.dataset_metrics.cell_id)
            bundle_name: str = parsed_metrics.dataset_metrics.cell_id
        else:
            tags.append(parsed_metrics.dataset_metrics.sample_internal_id)
            bundle_name: str = parsed_metrics.dataset_metrics.sample_internal_id
        return PacBioFileData(
            bundle_name=bundle_name,
            file_path=file_path,
            tags=tags,
        )

    def _is_file_type_smrt_cell(self, file_path: Path) -> bool:
        return self._get_bundle_type_for_file(file_path) == PacBioBundleTypes.SMRT_CELL
