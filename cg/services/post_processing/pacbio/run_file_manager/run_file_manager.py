from pathlib import Path

from cg.constants import FileExtensions
from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.post_processing.abstract_classes import RunFileManager
from cg.services.post_processing.error_handlers import (
    handle_post_processing_errors,
)
from cg.services.post_processing.exc import PostProcessingRunFileManagerError
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.post_processing.validators import validate_files_exist
from cg.utils.files import get_files_matching_pattern


class PacBioRunFileManager(RunFileManager):

    @handle_post_processing_errors(
        to_except=(FileNotFoundError,), to_raise=PostProcessingRunFileManagerError
    )
    def get_files_to_parse(self, run_data: PacBioRunData) -> list[Path]:
        """Get the file paths required by the PacBioMetricsParser."""
        run_path: Path = run_data.full_path
        files_to_parse: list[Path] = [self._find_ccs_report_file(run_path)]
        files_to_parse.extend(self._get_report_files(run_path))
        return files_to_parse

    @handle_post_processing_errors(
        to_except=(FileNotFoundError,), to_raise=PostProcessingRunFileManagerError
    )
    def get_files_to_store(self, run_data: PacBioRunData) -> list[Path]:
        """Get the files to store for the PostProcessingHKService."""
        run_path: Path = run_data.full_path
        files_to_store: list[Path] = self._find_hifi_files(run_path)
        files_to_store.extend(self.get_files_to_parse(run_data))
        return files_to_store

    @staticmethod
    def _find_ccs_report_file(run_path: Path) -> Path:
        """Return the path to the CCS report file."""
        statistics_dir: Path = Path(run_path, PacBioDirsAndFiles.STATISTICS_DIR)
        files: list[Path] = get_files_matching_pattern(
            directory=statistics_dir, pattern=f"*{PacBioDirsAndFiles.CCS_REPORT_SUFFIX}"
        )
        if not files:
            raise FileNotFoundError(f"No CCS report file found in {statistics_dir}")
        return files[0]

    @staticmethod
    def _get_report_files(run_path: Path) -> list[Path]:
        """Return the paths to the unzipped report files."""
        unzipped_dir: Path = Path(
            run_path, PacBioDirsAndFiles.STATISTICS_DIR, PacBioDirsAndFiles.UNZIPPED_REPORTS_DIR
        )
        report_files: list[Path] = [
            Path(unzipped_dir, PacBioDirsAndFiles.CONTROL_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.LOADING_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.RAW_DATA_REPORT),
            Path(unzipped_dir, PacBioDirsAndFiles.SMRTLINK_DATASETS_REPORT),
        ]
        validate_files_exist(report_files)
        return report_files

    @staticmethod
    def _find_hifi_files(run_path: Path) -> list[Path]:
        """Return the paths to the HiFi read files."""
        hifi_dir = Path(run_path, PacBioDirsAndFiles.HIFI_READS)
        bam_files: list[Path] = get_files_matching_pattern(
            directory=hifi_dir, pattern=f"*{FileExtensions.BAM}*"
        )
        if len(bam_files) != 2:
            raise FileNotFoundError(
                f"Expected 2 HiFi read files in {hifi_dir}, found {len(bam_files)}"
            )
        validate_files_exist(bam_files)
        return bam_files
