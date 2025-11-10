from collections.abc import Iterator

from cg.constants.sequencing import SequencingPlatform
from cg.constants.symbols import EMPTY_STRING
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, Sample

HEADERS: list[str] = [
    "sample",
    "run_accession",
    "instrument_platform",
    "fastq_1",
    "fastq_2",
    "fasta",
]


class TaxprofilerSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Return formatted information required to build a sample sheet for a case.
        This contains information for all samples linked to the case."""
        case: Case = self.store.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for sample in case.samples:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(sample))
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, sample: Sample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        content: list[list[str]] = []
        paired_fastq_files: Iterator[tuple[str, str]] = self._get_paired_read_paths(sample)
        for incremental_id, (forward_file, reverse_file) in enumerate(paired_fastq_files, start=1):
            entry: list[str] = [
                sample.name,
                incremental_id,
                SequencingPlatform.ILLUMINA,
                forward_file,
                reverse_file,
                EMPTY_STRING,
            ]
            content.append(entry)
        return content
