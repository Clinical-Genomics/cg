from datetime import datetime

from pydantic import BaseModel


class LaneMetric(BaseModel):
    """Model for lane specific sequencing metrics."""

    lane: int
    number_of_reads: int
    _yield: int | None = None


class ConcatenatedLaneMetric(BaseModel):
    """Model for concatenated lane sequencing metrics."""

    number_of_reads: int
    _yield: int | None = None


class DNACoverageMetric(BaseModel):
    """Coverage metrics from the pipeline output."""

    mean_target_coverage: float | None = None
    median_target_coverage: float | None = None
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


class RNACoverageMetric(BaseModel):
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


class SequencingMetric(BaseModel):
    """Model for collecting sample specific reads information."""

    total_reads: list[LaneMetric] | ConcatenatedLaneMetric
    mapped_reads: list[LaneMetric] | ConcatenatedLaneMetric
    percentage_mapped_reads: list[float] | float
    coverage_metric: DNACoverageMetric | RNACoverageMetric
    pct_duplication: float | None = None
    pct_adapter: float | None


class RareDiseaseDNAMetric(BaseModel):
    sex: str


class RareDiseaseRNAMetric(BaseModel):
    pass


class BalsamicMetric(BaseModel):
    pass


class RNAFusionMetric(BaseModel):
    pass


class SampleQCMetric(BaseModel):
    """Sample qc metrics from pipeline outputs."""

    sample_id: str
    sequencing_metric: list[SequencingMetric]
    pipeline_specific_metric: RareDiseaseDNAMetric | BalsamicMetric | RNAFusionMetric | RareDiseaseRNAMetric


class CaseQCMetric(BaseModel):
    """Case qc metrics from a pipeline run."""

    run_time: datetime
    cpu_hours: int
    memory_used_gb: int


class Pipeline(BaseModel):
    """Model for pipeline information."""

    name: str
    version: str


class PipelineQCMetric(BaseModel):
    """Model for collecting pipeline qc metrics."""

    case_id: str
    case_qc_metrics: CaseQCMetric
    sample_qc_metrics: list[SampleQCMetric]
    pipeline: Pipeline
