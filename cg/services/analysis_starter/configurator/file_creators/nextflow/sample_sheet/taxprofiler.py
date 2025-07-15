from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowSampleSheetCreator,
)
from cg.store.models import Case, CaseSample

HEADERS: list[str] = [
    "sample",
    "run_accession",
    "instrument_platform",
    "fastq_1",
    "fastq_2",
    "fasta",
]


class TaxprofilerSampleSheetCreator(NextflowSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        content: list[list[str]] = []
        sample_name: str = case_sample.sample.name
        fastq_file_pairs: list[tuple[str, str]] = self._get_validated_and_existing_fastq_paths(
            sample=case_sample.sample
        )

        for run_accession, (forward_file, reverse_file) in enumerate(fastq_file_pairs, 1):
            entry: list[str] = [
                sample_name,
                run_accession,
                SequencingPlatform.ILLUMINA,
                forward_file,
                reverse_file,
                EMPTY_STRING,
            ]
            content.append(entry)
        return content
