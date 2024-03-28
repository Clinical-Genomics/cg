from enum import StrEnum

from cg.constants.constants import Strandedness
from cg.models.nf_analysis import NextflowSampleSheetEntry


class TomteSampleSheetEntry(NextflowSampleSheetEntry):
    """Tomte sample model is used when building the sample sheet."""

    case_id: str
    strandedness: Strandedness

    @property
    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of lists, where
        each list represents a line in the final file."""
        return [
            [
                self.case_id,
                self.name,
                fastq_forward_read_path,
                fastq_reverse_read_path,
                str(self.strandedness),
            ]
            for fastq_forward_read_path, fastq_reverse_read_path in zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            )
        ]


class TomteSampleSheetHeaders(StrEnum):
    case_id: str = "case"
    name: str = "sample"
    fastq_1: str = "fastq_1"
    fastq_2: str = "fastq_2"
    strandedness: str = "strandedness"

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda header: header.value, cls))
