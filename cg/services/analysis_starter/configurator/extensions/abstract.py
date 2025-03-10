from abc import ABC, abstractmethod
from pathlib import Path


class PipelineExtension(ABC):

    @abstractmethod
    def configure(self, case_id: str, case_path: Path):
        pass
