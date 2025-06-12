from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.pacbio import MANIFEST_FILE_PATTERN, ZIPPED_REPORTS_PATTERN, PacBioDirsAndFiles
from cg.services.run_devices.abstract_classes import RunFileManager
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import PostProcessingRunFileManagerError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_file_manager.models import PacBioRunValidatorFiles
from cg.services.run_devices.validators import validate_files_or_directories_exist
from cg.utils.files import get_files_matching_pattern


class PacBioRunFileManager(RunFileManager):

    @handle_post_processing_errors(
        to_except=(FileNotFoundError,), to_raise=PostProcessingRunFileManagerError
    )
    def get_files_to_parse(self, run_data: PacBioRunData) -> list[Path]:
        """Get the file paths required by the PacBioMetricsParser."""
        run_path: Path = run_data.full_path
        validate_files_or_directories_exist([run_path])
        return self._get_report_files(run_path)

    @handle_post_processing_errors(
        to_except=(FileNotFoundError,), to_raise=PostProcessingRunFileManagerError
    )
    def get_files_to_store(self, run_data: PacBioRunData) -> list[Path]:
        """Get the files to store for the PostProcessingHKService."""
        run_path: Path = run_data.full_path
        return self.get_files_to_parse(run_data) + self._get_hifi_read_files(run_path)

    @handle_post_processing_errors(
        to_except=(FileNotFoundError,), to_raise=PostProcessingRunFileManagerError
    )
    def get_run_validation_files(self, run_data: PacBioRunData) -> PacBioRunValidatorFiles:
        manifest_file: Path = self._get_manifest_file(run_data.full_path)
        decompression_target: Path = self._get_zipped_reports_file(run_data.full_path)
        decompression_destination: Path = self._get_unzipped_reports_dir(run_data.full_path)
        return PacBioRunValidatorFiles(
            manifest_file=manifest_file,
            decompression_target=decompression_target,
            decompression_destination=decompression_destination,
        )

    def _get_ccs_report_file(self, run_path: Path) -> Path:
        """Return the path to the CCS report file."""
        statistics_dir: Path = self._get_statistics_dir(run_path)
        files: list[Path] = get_files_matching_pattern(
            directory=statistics_dir, pattern=f"*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}"
        )
        if not files:
            raise FileNotFoundError(f"No CCS report file found in {statistics_dir}")
        return files[0]

    def _get_report_files(self, run_path: Path) -> list[Path]:
        """Return the paths to the report files."""
        unzipped_dir: Path = self._get_unzipped_reports_dir(run_path)
        report_files: list[Path] = [
            Path(unzipped_dir, PacBioDirsAndFiles.BARCODES_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.CONTROL_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.LOADING_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.RAW_DATA_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT),
            self._get_ccs_report_file(run_path),
        ]
        validate_files_or_directories_exist(report_files)
        return report_files

    @staticmethod
    def _remove_unassigned_bam_file(bam_files: list[Path]) -> list[Path]:
        """Remove the unassigned bam file from the file list."""
        return [file for file in bam_files if "unassigned" not in file.name]

    def _get_hifi_read_files(self, run_path: Path) -> list[Path]:
        """Return the path to the HiFi read file."""
        hifi_dir = Path(run_path, PacBioDirsAndFiles.HIFI_READS)
        bam_files: list[Path] = get_files_matching_pattern(
            directory=hifi_dir, pattern=f"*{FileExtensions.BAM}"
        )
        barcoded_files: list[Path] = self._remove_unassigned_bam_file(bam_files)
        validate_files_or_directories_exist(barcoded_files)
        return barcoded_files

    @staticmethod
    def _get_unzipped_reports_dir(run_path) -> Path:
        return Path(
            run_path, PacBioDirsAndFiles.STATISTICS_DIR, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR
        )

    @staticmethod
    def _get_statistics_dir(run_path) -> Path:
        return Path(run_path, PacBioDirsAndFiles.STATISTICS_DIR)

    @staticmethod
    def _get_manifest_file(run_path) -> Path:
        file_list: list[Path] = get_files_matching_pattern(
            directory=Path(run_path, PacBioDirsAndFiles.METADATA_DIR), pattern=MANIFEST_FILE_PATTERN
        )
        if not file_list:
            raise FileNotFoundError(f"No Manifest file found in {run_path}")
        return file_list[0]

    def _get_zipped_reports_file(self, run_path) -> Path:
        return get_files_matching_pattern(
            directory=self._get_statistics_dir(run_path),
            pattern=ZIPPED_REPORTS_PATTERN,
        )[0]
