from abc import ABC, abstractmethod
from pathlib import Path


class ParamsFileCreator(ABC):

    def __init__(self, params: str):
        self.params = Path(params)

    @abstractmethod
    def create(self, case_id: str, file_path: Path, sample_sheet_path: Path) -> any:
        pass
