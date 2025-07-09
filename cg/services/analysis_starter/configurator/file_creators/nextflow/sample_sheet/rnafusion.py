from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import Strandedness
from cg.models.rnafusion.rnafusion import RnafusionSampleSheetEntry
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


class RNAFusionSampleSheetCreator(NextflowSampleSheetCreator):
    def __init__(self, housekeeper_api: HousekeeperAPI, store: Store):
        super().__init__(housekeeper_api)
        self.store = store

    def _get_content(self, case_id: str) -> list[list[str]]:
        content = [RnafusionSampleSheetEntry.headers()]
        case: Case = self.store.get_case_by_internal_id(case_id)
        for sample in case.samples:
            content.extend(self._get_sample_content(sample))
        return content

    def _get_sample_content(self, sample: Sample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        fastq_forward_read_paths, fastq_reverse_read_paths = self._get_paired_read_paths(sample)
        sample_sheet_entry = RnafusionSampleSheetEntry(
            name=sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            strandedness=Strandedness.REVERSE,
        )
        return sample_sheet_entry.reformat_sample_content()
