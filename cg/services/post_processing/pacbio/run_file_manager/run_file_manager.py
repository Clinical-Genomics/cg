from pathlib import Path

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.services.post_processing.abstract_classes import RunFileManager
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData
from cg.utils.files import get_files_matching_pattern


class PacBioRunFileManager(RunFileManager):

    def get_files_to_parse(self, run_data: PacBioRunData) -> list[Path]:
        """Get the files required for the PostProcessingMetricsService."""
        run_path: Path = run_data.full_path
        statistics_dir: Path = Path(run_path, PacBioDirsAndFiles.STATISTICS_DIR)
        zipped_dir: Path = Path(statistics_dir, PacBioDirsAndFiles.ZIPPER_DIR)
        ccs_report_file: Path = self._find_ccs_report_file(statistics_dir)
        return [ccs_report_file]

    def get_files_to_store(self, run_data: PacBioRunData) -> list[Path]:
        """Get the files to store for the PostProcessingHKService."""
        # BAM files
        self._find_bam_files()
        # Report files

    @staticmethod
    def _find_ccs_report_file(run_path: Path) -> Path:
        """Return the path to the the CCS report file."""
        files: list[Path] = get_files_matching_pattern(
            directory=run_path, pattern=PacBioDirsAndFiles.CCS_REPORT_SUFFIX
        )
        if not files:
            raise FileNotFoundError(f"No CCS report file found in {run_path}")
        return files[0]

    def _find_bam_files(self) -> list[Path]:
        """Return the paths to the BAM files."""
        pass
