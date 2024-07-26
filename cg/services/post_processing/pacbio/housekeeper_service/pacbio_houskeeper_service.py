"""Module for the PacBioHousekeeperService used in the Post processing flow."""

from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.pacbio import file_pattern_to_tag, file_pattern_to_bundle_type, PacBioBundleTypes
from cg.services.post_processing.abstract_classes import PostProcessingHKService
from cg.services.post_processing.pacbio.housekeeper_service.models import PacBioFileData
from cg.services.post_processing.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.post_processing.pacbio.metrics_parser.models import PacBioMetrics
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
        for file_path in file_to_store:
            bundle_info: PacBioFileData = self._create_bundle_info(
                file_path=file_path, parsed_metrics=parsed_metrics
            )
            self.hk_api.create_bundle_add_file_with_tags(
                bundle_name=bundle_info.bundle_name,
                file_path=bundle_info.file_path,
                tags=bundle_info.tags,
            )

    @staticmethod
    def _get_tags_for_file(file_path: Path) -> list[str]:
        for pattern in file_pattern_to_tag.keys():
            if pattern in file_path.as_posix():
                return file_pattern_to_tag[pattern]
        raise ValueError

    @staticmethod
    def _get_bundle_type_for_file(file_path: Path) -> str:
        for pattern in file_pattern_to_bundle_type.keys():
            if pattern in file_path.as_posix():
                return file_pattern_to_bundle_type[pattern]
        raise ValueError

    @staticmethod
    def _add_smrt_cell_id_to_tags(tags: list[str], parsed_metrics: PacBioMetrics) -> list[str]:
        tags.append(parsed_metrics.dataset_metrics.cell_id)
        return tags

    @staticmethod
    def _add_sample_id_to_tags(tags: list[str], parsed_metrics: PacBioMetrics) -> list[str]:
        tags.append(parsed_metrics.dataset_metrics.sample_internal_id)
        return tags

    def _create_bundle_info(self, file_path: Path, parsed_metrics: PacBioMetrics) -> PacBioFileData:
        tags: list[str] = self._get_tags_for_file(file_path)
        if self._is_file_type_smrt_cell(file_path):
            tags: list[str] = self._add_smrt_cell_id_to_tags(
                tags=tags, parsed_metrics=parsed_metrics
            )
            return PacBioFileData(
                bundle_name=parsed_metrics.dataset_metrics.cell_id, file_path=file_path, tags=tags
            )
        tags: list[str] = self._add_sample_id_to_tags(tags=tags, parsed_metrics=parsed_metrics)
        return PacBioFileData(
            bundle_name=parsed_metrics.dataset_metrics.sample_internal_id,
            file_path=file_path,
            tags=tags,
        )

    def _is_file_type_smrt_cell(self, file_path: Path) -> bool:
        return self._get_bundle_type_for_file(file_path) == PacBioBundleTypes.SMRT_CELL
