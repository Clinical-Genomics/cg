from abc import ABC, abstractmethod
from pathlib import Path

from cg.constants import FileExtensions


class NextflowFileCreator(ABC):

    def create(self, case_id: str, case_path: Path, dry_run: bool = False) -> None:
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: any = self._get_file_content(case_id=case_id)
        self._write_content_to_file_or_stdout(content=content, file_path=file_path, dry_run=dry_run)

    @staticmethod
    @abstractmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        pass

    @abstractmethod
    def _get_file_content(self, case_id: str) -> any:
        pass

    @staticmethod
    @abstractmethod
    def _write_content_to_file_or_stdout(content: any, file_path: Path, dry_run: bool) -> None:
        pass

    @staticmethod
    def _get_sample_sheet_path(case_id: str, case_path: Path) -> Path:
        """Path to sample sheet."""
        return Path(case_path, f"{case_id}_samplesheet").with_suffix(FileExtensions.CSV)
