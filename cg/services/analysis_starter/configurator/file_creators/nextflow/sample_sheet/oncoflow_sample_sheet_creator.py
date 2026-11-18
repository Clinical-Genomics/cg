from cg.exc import SampleSheetContentError
from cg.models.fastq import FastqFileMeta
from cg.services.analysis_starter.configurator.file_creators.nextflow.sample_sheet.creator import (
    NextflowFastqSampleSheetCreator,
)
from cg.store.models import Case, CaseSample, Sample

HEADERS: list[str] = [
    "group_id",
    "subject_id",
    "sample_id",
    "sample_type",
    "sequence_type",
    "filetype",
    "info",
    "filepath",
]


class OncoflowSampleSheetCreator(NextflowFastqSampleSheetCreator):

    def _get_content(self, case_id: str) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single case."""
        case: Case = self.store.get_case_by_internal_id_strict(internal_id=case_id)
        sample_sheet_content: list[list[str]] = [HEADERS]
        for link in case.links:
            sample_sheet_content.extend(self._get_sample_sheet_content_per_sample(case_sample=link))
        if sample_sheet_content == [HEADERS]:
            raise SampleSheetContentError(f"Sample sheet for case {case_id} is empty.")
        return sample_sheet_content

    def _get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        content: list[list[str]] = []
        paired_fastq_metadata: list[tuple[FastqFileMeta]] = self._get_paired_fastq_metadata(
            case_sample.sample
        )
        for forward_metadata, reverse_metadata in paired_fastq_metadata:
            content.append(
                [
                    case_sample.case.internal_id,
                    case_sample.case.internal_id,
                    case_sample.sample.name,
                    "tumor" if case_sample.sample.is_tumour else "normal",
                    "dna",
                    "fastq",
                    # TODO: Implement checks that lane and FC are the same in forward and reverse?
                    f"library_id:{forward_metadata.flow_cell_id};lane:{forward_metadata.lane}",
                    f"{forward_metadata.path.as_posix()};{reverse_metadata.path.as_posix()}",
                ]
            )
        return content

    def _get_paired_fastq_metadata(self, sample: Sample) -> list[tuple[FastqFileMeta]]:
        """Return a list of tuples with paired fastq metadata for the forward and reverse read."""
        sample_metadata: list[FastqFileMeta] = self._get_fastq_metadata_for_sample(sample)
        sorted_metadata: list[FastqFileMeta] = sorted(sample_metadata, key=lambda k: k.path)
        forward_metadata: list[FastqFileMeta] = [
            metadata for metadata in sorted_metadata if metadata.read_direction == 1
        ]
        reverse_metadata: list[FastqFileMeta] = [
            metadata for metadata in sorted_metadata if metadata.read_direction == 2
        ]
        return list(zip(forward_metadata, reverse_metadata))
