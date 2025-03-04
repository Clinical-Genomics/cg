from abc import ABC, abstractmethod
from pathlib import Path


class FileContentCreator(ABC):

    @abstractmethod
    def create(self, case_path: Path) -> any:
        pass
