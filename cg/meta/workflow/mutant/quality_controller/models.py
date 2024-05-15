from pydantic import BaseModel

from cg.meta.workflow.mutant.metadata_parser.models import SamplesMetadataMetrics
from cg.meta.workflow.mutant.metrics_parser.models import SamplesResultsMetrics


class QualityMetrics(BaseModel):
    samples_results: SamplesResultsMetrics
    samples_metadata: SamplesMetadataMetrics

    @property
    def sample_ids(self):
        return self.samples_metadata.keys() #samples_metadata includes internal_negative_control


class SampleQualityResult(BaseModel):
    sample_id: str
    passes_qc: bool
    is_external_negative_control: bool
    is_internal_negative_control: bool
    passes_reads_threshold: bool
    passes_mutant_qc: bool = False


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
