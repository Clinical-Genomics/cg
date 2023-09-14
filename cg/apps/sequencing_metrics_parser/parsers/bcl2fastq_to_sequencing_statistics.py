from datetime import datetime
from pathlib import Path
from typing import List, Tuple

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


def create_bcl2fastq_metrics(bcl2fastq_flow_cell_path: Path) -> List[SampleLaneSequencingMetrics]:
    """Return sequencing metrics for a bcl2fastq flow cell."""
    raw_metrics: List[SampleLaneMetrics] = parse_metrics(bcl2fastq_flow_cell_path)
    return convert_to_sequencing_metrics(raw_metrics)


def create_bcl2fastq_undetermined_metrics(
    bcl2fastq_flow_cell_path: Path, non_pooled_lane_sample_pairs: List[Tuple[str, int]]
) -> List[SampleLaneSequencingMetrics]:
    """Return undetermined sequencing metrics for a bcl2fastq flow cell."""
    undetermined_metrics: List[SampleLaneMetrics] = parse_undetermined_non_pooled_metrics(
        flow_cell_dir=bcl2fastq_flow_cell_path,
        non_pooled_lane_sample_pairs=non_pooled_lane_sample_pairs,
    )
    return convert_to_sequencing_metrics(undetermined_metrics)


def convert_to_sequencing_metrics(
    raw_metrics: List[SampleLaneMetrics],
) -> List[SampleLaneSequencingMetrics]:
    """Convert the raw bcl2fastq metrics to SampleLaneSequencingMetrics."""
    return [create_sequencing_metric(raw_metric) for raw_metric in raw_metrics]


def create_sequencing_metric(
    raw_metric: SampleLaneMetrics,
) -> SampleLaneSequencingMetrics:
    """Generates a SampleLaneSequencingMetrics based on the provided raw results."""

    sample_base_percentage_passing_q30: float = calculate_q30_bases_percentage(
        q30_yield=raw_metric.total_yield_q30,
        total_yield=raw_metric.total_yield,
    )
    sample_base_mean_quality_score: float = calculate_average_quality_score(
        total_quality_score=raw_metric.total_quality_score,
        total_yield=raw_metric.total_yield,
    )

    return SampleLaneSequencingMetrics(
        flow_cell_name=raw_metric.flow_cell_name,
        flow_cell_lane_number=raw_metric.lane,
        sample_internal_id=raw_metric.sample_id,
        sample_total_reads_in_lane=raw_metric.total_reads,
        sample_base_percentage_passing_q30=sample_base_percentage_passing_q30,
        sample_base_mean_quality_score=sample_base_mean_quality_score,
        created_at=datetime.now(),
    )
