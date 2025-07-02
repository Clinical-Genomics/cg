from enum import StrEnum

from cg.models.nf_analysis import NextflowSampleSheetEntry


class RarediseaseSampleSheetEntry(NextflowSampleSheetEntry):
    """Raredisease sample model is used when building the sample sheet."""

    phenotype: int
    sex: int
    paternal_id: str
    maternal_id: str
    case_id: str

    @property
    def reformat_sample_content(self) -> list[list[str]]:
        """
        Reformat sample sheet content as a list of lists, where each list represents a
        line in the final file.
        """
        return [
            [
                self.name,
                lane + 1,
                forward_path,
                reverse_path,
                self.sex,
                self.phenotype,
                self.paternal_id,
                self.maternal_id,
                self.case_id,
            ]
            for lane, (forward_path, reverse_path) in enumerate(
                zip(self.fastq_forward_read_paths, self.fastq_reverse_read_paths)
            )
        ]


class RarediseaseSampleSheetHeaders(StrEnum):
    sample: str = "sample"
    lane: str = "lane"
    fastq_1: str = "fastq_1"
    fastq_2: str = "fastq_2"
    sex: str = "sex"
    phenotype: str = "phenotype"
    paternal_id: str = "paternal_id"
    maternal_id: str = "maternal_id"
    case_id: str = "case_id"

    @classmethod
    def list(cls) -> list[str]:
        return list(map(lambda header: header.value, cls))
