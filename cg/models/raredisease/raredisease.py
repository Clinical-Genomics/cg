from pathlib import Path

from pydantic.v1 import Field

from cg.models.nf_analysis import NextflowSampleSheetEntry


class RarediseaseSampleSheetEntry(NextflowSampleSheetEntry):
    """Raredisease sample model is used when building the sample sheet."""

    sex: str
    phenotype: int
    sex: int
    paternal_id: str
    maternal_id: str
    case_id: str

    @staticmethod
    def headers() -> list[str]:
        """Return sample sheet headers."""
        return [
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

    def reformat_sample_content(self) -> list[list[str]]:
        """Reformat sample sheet content as a list of list, where each list represents a line in the final file."""
        return [
            [
                self.name,
                lane + 1,
                self.fastq_forward_read_paths,
                self.fastq_reverse_read_paths,
                self.sex,
                self.phenotype,
                self.paternal_id,
                self.maternal_id,
                self.case_id,
            ]
            for lane, (self.fastq_forward_read_paths, self.fastq_reverse_read_paths) in enumerate(
                zip(self.fastq_forward_read_paths, self.fastq_reverse_read_paths)
            )
        ]
