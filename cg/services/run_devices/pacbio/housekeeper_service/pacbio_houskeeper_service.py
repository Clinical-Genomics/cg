"""Module for the PacBioHousekeeperService used in the Post processing flow."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import FileExtensions
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.constants.pacbio import (
    PacBioBundleTypes,
    PacBioDirsAndFiles,
    PacBioHousekeeperTags,
    file_pattern_to_bundle_type,
)
from cg.services.run_devices.abstract_classes import PostProcessingHKService
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import (
    PostProcessingParsingError,
    PostProcessingRunFileManagerError,
    PostProcessingStoreFileError,
)
from cg.services.run_devices.pacbio.housekeeper_service.models import PacBioFileData
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.metrics_parser.models import PacBioMetrics
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.utils.mapping import get_item_by_pattern_in_source

LOG = logging.getLogger(__name__)


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

    @handle_post_processing_errors(
        to_except=(PostProcessingRunFileManagerError, PostProcessingParsingError),
        to_raise=PostProcessingStoreFileError,
    )
    def store_files_in_housekeeper(self, run_data: PacBioRunData, dry_run: bool = False) -> None:
        parsed_metrics: PacBioMetrics = self.metrics_parser.parse_metrics(run_data)
        file_to_store: list[Path] = self.file_manager.get_files_to_store(run_data)
        for file_path in file_to_store:
            bundle_info: PacBioFileData = self._create_bundle_info(
                file_path=file_path, parsed_metrics=parsed_metrics
            )
            if dry_run:
                LOG.info(f"Dry run: would have added {bundle_info.file_path} to Housekeeper.")
                continue
            self.hk_api.create_bundle_and_add_file_with_tags(
                bundle_name=bundle_info.bundle_name,
                file_path=bundle_info.file_path,
                tags=bundle_info.tags,
            )
        LOG.debug(f"Files stored in Housekeeper for run {run_data.sequencing_run_name}")

    @staticmethod
    def _get_bundle_type_for_file(file_path: Path) -> str:
        return get_item_by_pattern_in_source(
            source=file_path.name, pattern_map=file_pattern_to_bundle_type
        )

    @staticmethod
    def _get_sample_id_from_barcode(barcode: str, metrics: PacBioMetrics) -> str:
        full_barcode: str = f"{barcode}--{barcode}"
        for sample in metrics.samples:
            if sample.barcode_name == full_barcode:
                return sample.sample_internal_id
        raise PostProcessingStoreFileError(f"Sample not found for barcode: {barcode}")

    @staticmethod
    def _get_tags_for_file(file_path: Path) -> list[str]:
        file_pattern_to_tag: dict[str, list[str]] = {
            PacBioDirsAndFiles.BARCODES_REPORT: [PacBioHousekeeperTags.BARCODES_REPORT],
            PacBioDirsAndFiles.CONTROL_REPORT: [PacBioHousekeeperTags.CONTROL_REPORT],
            f".*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}$": [PacBioHousekeeperTags.CCS_REPORT],
            PacBioDirsAndFiles.LOADING_REPORT: [PacBioHousekeeperTags.LOADING_REPORT],
            PacBioDirsAndFiles.RAW_DATA_REPORT: [PacBioHousekeeperTags.RAWDATA_REPORT],
            PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT: [PacBioHousekeeperTags.DATASETS_REPORT],
            f"{PacBioDirsAndFiles.HIFI_READS}.*{FileExtensions.BAM}$": [AlignmentFileTag.BAM],
        }
        return get_item_by_pattern_in_source(source=file_path.name, pattern_map=file_pattern_to_tag)

    def _create_bundle_info(self, file_path: Path, parsed_metrics: PacBioMetrics) -> PacBioFileData:
        tags: list[str] = self._get_tags_for_file(file_path)
        tags.append(parsed_metrics.dataset_metrics.cell_id)
        if self._is_file_type_smrt_cell(file_path):
            bundle_name: str = parsed_metrics.dataset_metrics.cell_id
        else:
            sample_internal_id: str = self._get_sample_internal_id_from_file(
                file_path=file_path, parsed_metrics=parsed_metrics
            )
            tags.append(sample_internal_id)
            bundle_name: str = sample_internal_id
        return PacBioFileData(
            bundle_name=bundle_name,
            file_path=file_path,
            tags=tags,
        )

    def _get_sample_internal_id_from_file(
        self, file_path: Path, parsed_metrics: PacBioMetrics
    ) -> str:
        barcode: str = file_path.name.split(".")[-2]
        return self._get_sample_id_from_barcode(barcode=barcode, metrics=parsed_metrics)

    def _is_file_type_smrt_cell(self, file_path: Path) -> bool:
        return self._get_bundle_type_for_file(file_path) == PacBioBundleTypes.SMRT_CELL
