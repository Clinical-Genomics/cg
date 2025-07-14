from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.models.taxprofiler.taxprofiler import TaxprofilerSampleSheetEntry
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.store.models import Case, CaseSample


class TaxprofilerSampleSheetCreator(NextflowSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [TaxprofilerSampleSheetEntry.headers()]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        sample_name: str = case_sample.sample.name
        fastq_forward_read_paths, fastq_reverse_read_paths = self._get_paired_read_paths(
            sample=case_sample.sample
        )
        sample_sheet_entry = TaxprofilerSampleSheetEntry(
            name=sample_name,
            instrument_platform=SequencingPlatform.ILLUMINA,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            fasta=EMPTY_STRING,
        )
        return sample_sheet_entry.reformat_sample_content()
