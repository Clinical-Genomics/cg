import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.io.csv import write_csv
from cg.store.models import Case, CaseSample, Sample
from cg.store.store import Store

LOG = logging.getLogger(__name__)

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
    def __init__(self, housekeeper_api: HousekeeperAPI, status_db: Store) -> None:
        self.housekeeper_api = housekeeper_api
        self.status_db = status_db

    def create(self, case_id: str, file_path: Path) -> None:
        LOG.debug(f"Creating sample sheet for case {case_id}")
        content: list[list[str]] = self._get_content(case_id)
        write_csv(content=content, file_path=file_path)

    def _get_content(self, case_id: str) -> list[list[str]]:
        case: Case = self.status_db.get_case_by_internal_id_strict(case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        read_file_paths: list[str] = self._get_bam_read_file_paths(sample=case_sample.sample)
        sample_sheet_entries = []

        for bam_path in read_file_paths:
            sample_sheet_entry: list[str] = [
                case_sample.case.internal_id,
                case_sample.sample.internal_id,
                bam_path,
                case_sample.case.internal_id,
                case_sample.get_paternal_sample_id or "0",
                case_sample.get_maternal_sample_id or "0",
                PlinkSex[case_sample.sample.sex.upper()].value,
                str(PlinkPhenotypeStatus[case_sample.status.upper()]),
            ]
            sample_sheet_entries.append(sample_sheet_entry)
        return sample_sheet_entries

    def _get_bam_read_file_paths(self, sample: Sample) -> list[str]:
        """Gather BAM file path for a sample based on the BAM tag."""
        return [
            hk_file.full_path
            for hk_file in self.housekeeper_api.files(bundle=sample.internal_id, tags={"bam"})
        ]
