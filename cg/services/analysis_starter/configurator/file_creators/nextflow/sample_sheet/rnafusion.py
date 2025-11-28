from collections.abc import Iterator

from cg.constants.constants import Strandedness
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, Sample

HEADERS: list[str] = ["sample", "fastq_1", "fastq_2", "strandedness"]


class RNAFusionSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        content: list[list[str]] = [HEADERS]
        case: Case = self.store.get_case_by_internal_id(case_id)
        for sample in case.samples:
            content.extend(self._get_sample_sheet_content_per_sample(sample))
        return content

    def _get_sample_sheet_content_per_sample(self, sample: Sample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        paired_fastq_files: Iterator[tuple[str, str]] = self._get_paired_read_paths(sample)
        content: list[list[str]] = []
        for fastq_forward_read_path, fastq_reverse_read_path in paired_fastq_files:
            content.append(
                [
                    sample.internal_id,
                    fastq_forward_read_path,
                    fastq_reverse_read_path,
                    Strandedness.REVERSE,
                ]
            )
        return content
