from abc import ABC, abstractmethod
from pathlib import Path

from cg.constants import FileExtensions


class ParamsFileCreator(ABC):

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """Return the path to the params file for a case."""
        return Path(case_path, f"{case_id}_params_file").with_suffix(FileExtensions.YAML)

    @abstractmethod
    def create(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> any:
        pass
