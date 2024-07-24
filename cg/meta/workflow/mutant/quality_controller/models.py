from pydantic import BaseModel

# from cg.meta.workflow.mutant.metadata_parser.models import SamplesMetadataMetrics
from cg.meta.workflow.mutant.metrics_parser.models import SampleResults
from cg.store.models import Sample


class MutantPoolSamples(BaseModel):
    samples: list[Sample]
    external_negative_control: Sample
    internal_negative_control: Sample


class QualityMetrics(BaseModel):
    results: dict[str, SampleResults]
    pool: MutantPoolSamples

    # samples_metadata: SamplesMetadataMetrics

    # @property
    # def sample_id_list(self):
    #     return [sample.sample_internal_id for sample in self.samples_metadata.samples]

    # @property
    # def internal_negative_control_id(self):
    #     return self.samples_metadata.internal_negative_control.sample_internal_id


class SampleQualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    passes_reads_threshold: bool
    passes_mutant_qc: bool = False


class SampleQualityResults(BaseModel):
    samples: list[SampleQualityResult]
    internal_negative_control: SampleQualityResult
    external_negative_control: SampleQualityResult


class CaseQualityResult(BaseModel):
    passes_qc: bool
    internal_negative_control_passes_qc: bool
    external_negative_control_passes_qc: bool


class QualityResult(BaseModel):
    case: CaseQualityResult
    samples: list[SampleQualityResult]
    summary: str

    @property
    def passes_qc(self) -> bool:
        return self.case.passes_qc
