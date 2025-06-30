from pathlib import Path

from cg.constants import FileExtensions
from cg.io.csv import write_csv
from cg.store.models import Case
from cg.store.store import Store


class SampleMappingFileCreator:

    def __init__(self, store: Store):
        self.store = store

    @staticmethod
    def get_file_path(case_id: str, case_path: Path) -> Path:
        """
        Return the path to the sample mapping file.
        """
        return Path(case_path, f"{case_id}_customer_internal_mapping").with_suffix(
            FileExtensions.CSV
        )

    def create(self, case_id: str, case_path: Path) -> None:
        """
        Create a sample mapping file from the provided sample mapping dictionary.
        """
        file_path: Path = self.get_file_path(case_id=case_id, case_path=case_path)
        content: list[list[str]] = self._get_content(case_id)
        write_csv(file_path=file_path, content=content)

    def _get_content(self, case_id: str) -> list[list[str]]:
        """ """
        content: list[list[str]] = [["customer_id", "internal_id"]]
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        for link in case.links:
            sample = link.sample
            content.append([sample.name, sample.internal_id])
        return content
