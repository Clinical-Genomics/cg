from pathlib import Path

from cg.io.csv import write_csv
from cg.store.models import Case, CaseSample
from cg.store.store import Store

HEADERS: list[str] = [
    "project",
    "sample",
    "file",
    "family_id",
    "paternal_id",
    "maternal_id",
    "sex",
    "phenotype",
]


class NalloSampleSheetCreator:
    def __init__(self, status_db: Store) -> None:
        self.status_db = status_db

    def create(self, case_id: str, file_path: Path) -> None:
        write_csv(content="", file_path=file_path)

    def _get_content(self, case_id: str) -> list[list[str]]:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        read_file_paths = self.get_bam_read_file_paths(sample=case_sample.sample)
        sample_sheet_entries = []

        for bam_path in read_file_paths:
            sample_sheet_entry = NalloSampleSheetEntry(
                project=case_sample.case.internal_id,
                sample=case_sample.sample.internal_id,
                read_file=Path(bam_path),
                family_id=case_sample.case.internal_id,
                paternal_id=case_sample.get_paternal_sample_id or "0",
                maternal_id=case_sample.get_maternal_sample_id or "0",
                sex=self.get_sex_code(case_sample.sample.sex),
                phenotype=self.get_phenotype_code(case_sample.status),
            )
            sample_sheet_entries.extend(sample_sheet_entry.reformat_sample_content)
        return sample_sheet_entries
