from abc import ABC, abstractmethod
from pathlib import Path


class ParamsFileCreator(ABC):

    @staticmethod
    @abstractmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        pass

    @abstractmethod
    def create(self, case_id: str, case_path: Path, sample_sheet_path: Path) -> any:
        pass
