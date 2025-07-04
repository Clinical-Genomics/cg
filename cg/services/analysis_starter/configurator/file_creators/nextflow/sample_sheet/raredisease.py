from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.models import (
    RarediseaseSampleSheetEntry,
    RarediseaseSampleSheetHeaders,
)
from cg.store.models import Case, CaseSample
from cg.store.store import Store


class RarediseaseSampleSheetCreator(NextflowSampleSheetCreator):

    def __init__(self, housekeeper_api: HousekeeperAPI, store: Store):
        super().__init__(housekeeper_api)
        self.store = store

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [RarediseaseSampleSheetHeaders.list()]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        fastq_forward_read_paths, fastq_reverse_read_paths = self._get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=case_sample.sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=self._get_sex_code(case_sample.sample.sex),
            phenotype=self._get_phenotype_code(case_sample.status),
            paternal_id=case_sample.get_paternal_sample_id,
            maternal_id=case_sample.get_maternal_sample_id,
            case_id=case_sample.case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content

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
