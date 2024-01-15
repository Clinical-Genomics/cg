from pydantic import BaseModel


class LaneMetrics(BaseModel):
    """Model for lane specific sequencing metrics."""

    lane: int
    number_of_reads: int
    _yield: int | None = None


class ConcatenatedMetrics(BaseModel):
    """Model for concatenated lane sequencing metrics."""

    number_of_reads: int
    _yield: int | None = None


class CoverageMetrics(BaseModel):
    """Coverage metrics from the pipeline output."""

    mean_target_coverage: float | None = None
    median_target_coverage: float | None = None
    pct_duplication: float | None = None
    pct_target_bases_10x: float | None = None
    pct_target_bases_20x: float | None = None
    pct_target_bases_30x: float | None = None
    pct_target_bases_40x: float | None = None
    pct_target_bases_50x: float | None = None
    pct_target_bases_100x: float | None = None
    pct_target_bases_250x: float | None = None
    pct_target_bases_500x: float | None = None
    pct_target_bases_1000x: float | None = None
    gc_dropout: float | None = None
    at_dropout: float | None = None
    pct_off_bait: float | None = None
    pct_pf_reads_improper_pairs: float | None = None
    pct_chimeras: float | None = None


class SequencingMetrics(BaseModel):
    """Model for collecting sample specific reads information."""

    total_reads: list[LaneMetrics] | ConcatenatedMetrics
    mapped_reads: list[LaneMetrics] | ConcatenatedMetrics
    percentage_mapped_reads: list[float] | float
    coverage_metrics: CoverageMetrics


class MIPDNAMetrics(BaseModel):
    pass


class MIPRNAMetrics(BaseModel):
    pass


class BalsamicMetrics(BaseModel):
    pass


class RNAFusionMetrics(BaseModel):
    pass


class SampleQCMetrics(BaseModel):
    """Sample qc metrics from pipeline outputs."""

    sample_id: str
    sequencing_metrics: list[SequencingMetrics]
    coverage_metrics: CoverageMetrics
    pipeline_specific_metrics: MIPDNAMetrics | BalsamicMetrics | RNAFusionMetrics | MIPRNAMetrics


class CaseQCMetrics(BaseModel):
    """Case qc metrics from a pipeline run."""

    pass


class Pipeline(BaseModel):
    """Model for pipeline information."""

    name: str
    version: str


class PipelineQCMetrics(BaseModel):
    """Model for collecting pipeline qc metrics."""

    case_id: str
    case_qc_metrics: CaseQCMetrics
    sample_qc_metrics: list[SampleQCMetrics]
    pipeline: Pipeline
