from pathlib import Path

from pydantic.v1 import Field

from cg.models.nf_analysis import NextflowSampleSheetEntry, PipelineParameters


class RarediseaseSampleSheetEntry(NextflowSampleSheetEntry):
    """Raredisease sample model is used when building the sample sheet."""


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
                lane,
                fastq_forward_read_path,
                fastq_reverse_read_path,
                self.sex,
                self.phenotype,
                self.paternal_id,
                self.maternal_id,
                self.case_id,
            ]
            for lane, (fastq_forward_read_path, fastq_reverse_read_path) in enumerate(zip(
                self.fastq_forward_read_paths, self.fastq_reverse_read_paths
            ))
        ]

class RarediseaseParameters(PipelineParameters):
    """Model for Raredisease parameters."""

    input: Path = Field(..., alias="sample_sheet_path")
    outdir: Path
    databases: Path
