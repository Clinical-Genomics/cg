from pydantic import BaseModel


class LaneMetrics(BaseModel):
    """Model for lane specific sequencing metrics."""

    lane: int
    number_of_reads: int


class CoverageMetrics(BaseModel):
    """Coverage metrics from the pipeline output."""

    mean_target_coverage: float | None
    median_target_coverage: float | None
    pct_duplication: float | None
    pct_target_bases_10x: float | None
    pct_target_bases_20x: float | None
    pct_target_bases_30x: float | None
    pct_target_bases_40x: float | None
    pct_target_bases_50x: float | None
    pct_target_bases_100x: float | None
    pct_target_bases_250x: float | None
    pct_target_bases_500x: float | None
    pct_target_bases_1000x: float | None
    gc_dropout: float | None
    at_dropout: float | None
    pct_off_bait: float | None


class SequencingMetrics(BaseModel):
    """Model for collecting sample specific reads information."""

    total_reads: list[LaneMetrics]
    mapped_reads: list[LaneMetrics]
    percentage_mapped_reads: list[float]
    coverage_metrics: CoverageMetrics


class MIPDNAMetrics(BaseModel):
    pass


class BalsamicMetrics(BaseModel):
    pass


class RNAFusionMetrics(BaseModel):
    pass


class SampleQCMetrics(BaseModel):
    """Sample qc metrics from pipeline outputs."""

    sample_id: str
    sequencing_metrics: list[SequencingMetrics]
    coverage_metrics: list[CoverageMetrics]
    pipeline_specific_metrics: MIPDNAMetrics | BalsamicMetrics | RNAFusionMetrics


class Pipeline(BaseModel):
    """Model for pipeline information."""

    name: str
    version: str


class PipelineQCMetrics(BaseModel):
    """Model for collecting pipeline qc metrics."""

    case_id: str
    samples: list[SampleQCMetrics]
    pipeline: Pipeline
