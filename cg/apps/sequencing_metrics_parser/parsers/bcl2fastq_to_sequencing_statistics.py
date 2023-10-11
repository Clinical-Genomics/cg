from datetime import datetime
from pathlib import Path

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import SampleLaneMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import (
    parse_metrics,
    parse_undetermined_non_pooled_metrics,
)
from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_average_quality_score,
    calculate_q30_bases_percentage,
)
from cg.store.models import SampleLaneSequencingMetrics


def create_bcl2fastq_metrics(bcl2fastq_flow_cell_path: Path) -> list[SampleLaneSequencingMetrics]:
    """Return sequencing metrics for a bcl2fastq flow cell."""
    bcl2fastq_metrics: list[SampleLaneMetrics] = parse_metrics(bcl2fastq_flow_cell_path)
    return convert_to_sequencing_metrics(bcl2fastq_metrics)


def create_bcl2fastq_undetermined_metrics(
    bcl2fastq_flow_cell_path: Path, non_pooled_lane_sample_pairs: list[tuple[str, int]]
) -> list[SampleLaneSequencingMetrics]:
    """Return undetermined sequencing metrics for a bcl2fastq flow cell."""
    undetermined_metrics: list[SampleLaneMetrics] = parse_undetermined_non_pooled_metrics(
        flow_cell_dir=bcl2fastq_flow_cell_path,
        non_pooled_lane_sample_pairs=non_pooled_lane_sample_pairs,
    )
    return convert_to_sequencing_metrics(undetermined_metrics)


def convert_to_sequencing_metrics(
    bcl2fastq_metrics: list[SampleLaneMetrics],
) -> list[SampleLaneSequencingMetrics]:
    """Convert the raw bcl2fastq metrics to SampleLaneSequencingMetrics."""
    return [create_sequencing_metric(metric) for metric in bcl2fastq_metrics]


def create_sequencing_metric(
    bcl2fastq_metric: SampleLaneMetrics,
) -> SampleLaneSequencingMetrics:
    """Generates a SampleLaneSequencingMetrics based on the provided raw results."""

    sample_base_percentage_passing_q30: float = calculate_q30_bases_percentage(
        q30_yield=bcl2fastq_metric.total_yield_q30,
        total_yield=bcl2fastq_metric.total_yield,
    )
    sample_base_mean_quality_score: float = calculate_average_quality_score(
        total_quality_score=bcl2fastq_metric.total_quality_score,
        total_yield=bcl2fastq_metric.total_yield,
    )

    return SampleLaneSequencingMetrics(
        flow_cell_name=bcl2fastq_metric.flow_cell_name,
        flow_cell_lane_number=bcl2fastq_metric.lane,
        sample_internal_id=bcl2fastq_metric.sample_id,
        sample_total_reads_in_lane=bcl2fastq_metric.total_reads,
        sample_base_percentage_passing_q30=sample_base_percentage_passing_q30,
        sample_base_mean_quality_score=sample_base_mean_quality_score,
        created_at=datetime.now(),
    )
