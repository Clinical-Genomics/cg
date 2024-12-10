from abc import abstractmethod, ABC
from pathlib import Path


class PathNameFormatter(ABC):
    """
    Abstract class that encapsulates the logic required for formatting the path name.
    """

    @abstractmethod
    def format_file_path(self, file_path: Path, provided_id: str, provided_name: str) -> Path:
        """Format the file path."""
        pass
