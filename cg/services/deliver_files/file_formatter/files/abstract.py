from abc import abstractmethod, ABC
from pathlib import Path

from cg.services.deliver_files.file_fetcher.models import SampleFile, CaseFile
from cg.services.deliver_files.file_formatter.destination.models import FormattedFile


class FileFormatter(ABC):

    @abstractmethod
    def format_files(
        self, moved_files: list[CaseFile | SampleFile], delivery_path: Path
    ) -> list[FormattedFile]:
        """Format the files to deliver."""
        pass
