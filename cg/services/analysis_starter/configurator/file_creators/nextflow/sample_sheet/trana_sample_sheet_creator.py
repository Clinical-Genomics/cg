from cg.exc import SampleSheetContentError
from cg.models.fastq import FastqFileMeta
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, Sample

HEADERS: list[str] = ["sample", "fastq_1", "fastq_2", "control"]


class TranaSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:

        case: Case = self.store.get_case_by_internal_id_strict(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for sample in case.samples:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(sample))
        if sample_sheet_content == [HEADERS]:
            raise SampleSheetContentError(f"Sample sheet for case {case_id} is empty.")
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, sample: Sample):

        fastq_files = self._get_fastq_files_for_sample(sample)
        control: Sample = sample

        content = []

        pass

    def _get_fastq_files_for_sample(self, sample: Sample) -> list[str]:
        sample_metadata: list[FastqFileMeta] = self._get_fastq_metadata_for_sample(sample)
        fastq_paths: list[str] = self._extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        return fastq_paths
