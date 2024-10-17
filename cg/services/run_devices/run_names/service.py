from abc import ABC, abstractmethod


class RunNamesService(ABC):

    def __init__(self, run_directory: str):
        self.run_directory = run_directory

    @abstractmethod
    def get_run_names(self) -> list[str]:
        """Get all the run names from a run directory."""
        pass
