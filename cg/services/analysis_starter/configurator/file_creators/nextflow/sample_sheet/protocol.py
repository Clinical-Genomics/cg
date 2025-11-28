from abc import abstractmethod
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class SampleSheetCreator(Protocol):
    @abstractmethod
    def create(self, case_id: str, file_path: Path) -> None:
        raise NotImplementedError(
            "Please implement create to conform to the SampleSheetFileCreator protocol"
        )
