from pydantic import BaseModel


class SampleQualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_control: bool
    passes_reads_threshold: bool = True
    passes_mutant_qc: bool


class CaseQualityResult(BaseModel):
    passes_qc: bool
    control_passes_qc: bool


class QualityResult(BaseModel):
    case: CaseQualityResult
    samples: list[SampleQualityResult]
    summary: str

    @property
    def passes_qc(self) -> bool:
        return self.case.passes_qc
