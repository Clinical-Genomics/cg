from pathlib import Path

from cg.constants import FileExtensions


class RarediseaseSampleSheetCreator:

    def __init__(self):
        pass

    def create(self, case_id: str, case_path: Path, dry_run: bool = False) -> None:
        sample_sheet_content: list[list[any]] = self._get_sample_sheet_content(case_id=case_id)
        if not dry_run:
            self._write_sample_sheet(
                content=sample_sheet_content,
                file_path=self.get_sample_sheet_path(case_id=case_id, case_path=case_path),
                header=self.sample_sheet_headers,
            )

    @staticmethod
    def get_sample_sheet_path(case_id: str, case_path: Path) -> Path:
        """Path to sample sheet."""
        return Path(case_path, f"{case_id}_samplesheet").with_suffix(FileExtensions.CSV)
