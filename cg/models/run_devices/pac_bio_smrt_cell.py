from pathlib import Path


class PacBioRunDirectoryData:
    """Class to collect information about sequencing run directories and their particular files."""

    def __init__(self, sequencing_run_path: Path):
        self.path = sequencing_run_path

    def get_report_zip_file(self) -> Path | None:
        """Return the path to the report zip file."""
        statistics_dir = Path(self.path, "statistics")
        zip_files = list(statistics_dir.rglob("*.zip"))
        return zip_files[0] if zip_files else None
