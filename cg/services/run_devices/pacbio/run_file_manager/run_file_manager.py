from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.run_devices.abstract_classes import RunFileManager
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import PostProcessingRunFileManagerError
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
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

    @staticmethod
    def _get_ccs_report_file(run_path: Path) -> Path:
        """Return the path to the CCS report file."""
        statistics_dir: Path = Path(run_path, PacBioDirsAndFiles.STATISTICS_DIR)
        files: list[Path] = get_files_matching_pattern(
            directory=statistics_dir, pattern=f"*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}"
        )
        if not files:
            raise FileNotFoundError(f"No CCS report file found in {statistics_dir}")
        return files[0]

    def _get_report_files(self, run_path: Path) -> list[Path]:
        """Return the paths to the unzipped report files."""
        unzipped_dir: Path = Path(
            run_path, PacBioDirsAndFiles.STATISTICS_DIR, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR
        )
        report_files: list[Path] = [
            Path(unzipped_dir, PacBioDirsAndFiles.CONTROL_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.LOADING_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.RAW_DATA_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT),
            self._get_ccs_report_file(run_path),
        ]
        validate_files_or_directories_exist(report_files)
        return report_files

    @staticmethod
    def _get_hifi_read_files(run_path: Path) -> list[Path]:
        """Return the path to the HiFi read file."""
        hifi_dir = Path(run_path, PacBioDirsAndFiles.HIFI_READS)
        bam_files: list[Path] = get_files_matching_pattern(
            directory=hifi_dir, pattern=f"*{FileExtensions.BAM}"
        )
        validate_files_or_directories_exist(bam_files)
        return bam_files
