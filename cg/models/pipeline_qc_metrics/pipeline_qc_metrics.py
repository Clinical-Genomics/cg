from pydantic import BaseModel


class LaneMetrics(BaseModel):
    """Model for lane specific sequencing metrics."""

    lane: int
    number_of_reads: int
    _yield: int | None = None


class ConcatenatedLaneMetrics(BaseModel):
    """Model for concatenated lane sequencing metrics."""

    number_of_reads: int
    _yield: int | None = None


class DNACoverageMetrics(BaseModel):
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
    pct_adapter: float | None


class RNACoverageMetrics(BaseModel):
    """Coverage metrics for an RNA pipeline output."""

    after_filtering_gc_content: float | None
    after_filtering_q20_rate: float | None
    after_filtering_q30_rate: float | None
    after_filtering_read1_mean_length: float | None
    median_5prime_to_3prime_bias: float | None
    pct_adapter: float | None
    pct_mrna_bases: float | None
    pct_ribosomal_bases: float | None
    pct_surviving: float | None
    pct_duplication: float | None
    read_pairs_examined: float | None
    uniquely_mapped_percent: float | None


class SequencingMetrics(BaseModel):
    """Model for collecting sample specific reads information."""

    total_reads: list[LaneMetrics] | ConcatenatedLaneMetrics
    mapped_reads: list[LaneMetrics] | ConcatenatedLaneMetrics
    percentage_mapped_reads: list[float] | float
    coverage_metrics: DNACoverageMetrics | RNACoverageMetrics


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
