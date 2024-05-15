from pydantic import BaseModel


class SampleQualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_control: bool
    application_tag: str
    passes_reads_qc: bool
    passes_mapping_qc: bool = True
    passes_duplication_qc: bool = True
    passes_inserts_qc: bool = True
    passes_coverage_qc: bool = True
    passes_10x_coverage_qc: bool = True


class CaseQualityResult(BaseModel):
    passes_qc: bool
    control_passes_qc: bool
    urgent_passes_qc: bool
    non_urgent_passes_qc: bool


class QualityResult(BaseModel):
    case: CaseQualityResult
    samples: list[SampleQualityResult]
    summary: str

    @property
    def passes_qc(self) -> bool:
        return self.case.passes_qc
