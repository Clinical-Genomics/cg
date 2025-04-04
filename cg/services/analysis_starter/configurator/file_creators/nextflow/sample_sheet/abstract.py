from abc import ABC, abstractmethod
from pathlib import Path


class NextflowSampleSheetCreator(ABC):

    @staticmethod
    @abstractmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        pass

    @abstractmethod
    def create(self, case_id: str, case_path: Path) -> None:
        pass
