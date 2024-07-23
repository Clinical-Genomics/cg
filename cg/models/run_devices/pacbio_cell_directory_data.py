from pathlib import Path

from cg.constants.pacbio import PacBioDirsAndFiles
from cg.utils.files import get_files_in_directory_with_pattern


class PacBioCellDirectoryData:
    """Class to collect information about PacBio sequencing run directories."""

    def __init__(self, pac_bio_run_directory: Path):
        self.path = pac_bio_run_directory
        self.statistics_dir = Path(self.path, "statistics")

    @property
    def ccs_report(self) -> Path:
        """Returns the CCS report file path."""
        files: list[Path] = get_files_in_directory_with_pattern(
            directory=self.statistics_dir, pattern=PacBioDirsAndFiles.CCS_REPORT_SUFFIX
        )
        return files[0]
