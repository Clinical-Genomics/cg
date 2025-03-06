from abc import ABC, abstractmethod
from pathlib import Path


class FileCreator(ABC):

    @abstractmethod
    def create(self, case_id: str, case_path: Path) -> any:
        pass
