from pydantic import BaseModel
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.store.models import Sample


class MutantPoolSamples(BaseModel):
    samples: list[Sample]
    external_negative_control: Sample
    internal_negative_control: Sample


class QualityMetrics(BaseModel):
    results: dict[str, SampleResults]
    pool: MutantPoolSamples

class SampleQualityResults(BaseModel):
    sample_id: str
    passes_qc: bool
    passes_reads_threshold: bool
    passes_mutant_qc: bool = False


class SamplesQualityResults(BaseModel):
    samples: list[SampleQualityResults]
    internal_negative_control: SampleQualityResults
    external_negative_control: SampleQualityResults

    @property
    def total_samples_count(self) -> int:
        return len(self.samples)

    @property
    def passed_samples_count(self) -> int:
        samples_pass_qc: list[bool] = [sample_result.passes_qc for sample_result in self.samples]
        return sum(samples_pass_qc)

    @property
    def failed_samples_count(self) -> int:
        return self.total_samples_count - self.passed_samples_count


class CaseQualityResult(BaseModel):
    passes_qc: bool
    internal_negative_control_passes_qc: bool
    external_negative_control_passes_qc: bool


class QualityResult(BaseModel):
    case_quality_result: CaseQualityResult
    samples_quality_results: SamplesQualityResults
    summary: str

    @property
    def passes_qc(self) -> bool:
        return self.case_quality_result.passes_qc
