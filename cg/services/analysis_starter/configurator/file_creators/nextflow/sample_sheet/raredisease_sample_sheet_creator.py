from typing import Iterator

from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, CaseSample

HEADERS: list[str] = [
    "sample",
    "lane",
    "fastq_1",
    "fastq_2",
    "sex",
    "phenotype",
    "paternal_id",
    "maternal_id",
    "case_id",
]


class RarediseaseSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a raredisease case.
        This contains information for all samples linked to the case."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        content: list[list[str]] = []
        paired_fastq_paths: Iterator[tuple[str, str]] = self._get_paired_read_paths(
            case_sample.sample
        )
        for incremental_id, (fastq_forward_read_path, fastq_reverse_read_path) in enumerate(
            paired_fastq_paths, start=1
        ):
            content.append(
                [
                    case_sample.sample.internal_id,
                    incremental_id,
                    fastq_forward_read_path,
                    fastq_reverse_read_path,
                    str(self._get_sex_code(case_sample.sample.sex)),
                    str(self._get_phenotype_code(case_sample.status)),
                    case_sample.get_paternal_sample_id,
                    case_sample.get_maternal_sample_id,
                    case_sample.case.internal_id,
                ]
            )
        return content

    @staticmethod
    def _get_phenotype_code(phenotype: str) -> int:
        """Return Raredisease phenotype code."""
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def _get_sex_code(sex: str) -> PlinkSex:
        """Return Raredisease sex code."""
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code
