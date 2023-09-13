from datetime import datetime
from pathlib import Path
from typing import List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import SampleLaneMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import parse_bcl2fastq_sequencing_metrics
from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_average_quality_score,
    calculate_q30_bases_percentage,
)
from cg.store.models import SampleLaneSequencingMetrics


def create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell(
    flow_cell_dir: Path,
) -> List[SampleLaneSequencingMetrics]:
    """
    Parses the Bcl2fastq generated stats.json files and aggregates and calculates metrics for each sample in each lane.
    """

    sample_lane_sequencing_metrics: List[SampleLaneSequencingMetrics] = []
    sample_and_lane_metrics: List[SampleLaneMetrics] = parse_bcl2fastq_sequencing_metrics(
        flow_cell_dir=flow_cell_dir
    )

    for raw_sample_metrics in sample_and_lane_metrics:
        metrics: SampleLaneSequencingMetrics = create_sample_lane_sequencing_metrics_from_bcl2fastq(
            raw_sample_metrics
        )
        sample_lane_sequencing_metrics.append(metrics)

    return sample_lane_sequencing_metrics


def create_sample_lane_sequencing_metrics_from_bcl2fastq(
    sample_lane_metrics: SampleLaneMetrics,
) -> SampleLaneSequencingMetrics:
    """Generates a SampleLaneSequencingMetrics based on the provided raw results."""

    sample_base_percentage_passing_q30: float = calculate_q30_bases_percentage(
        q30_yield=sample_lane_metrics.total_yield_q30,
        total_yield=sample_lane_metrics.total_yield,
    )
    sample_base_mean_quality_score: float = calculate_average_quality_score(
        total_quality_score=sample_lane_metrics.total_quality_score,
        total_yield=sample_lane_metrics.total_yield,
    )

    return SampleLaneSequencingMetrics(
        flow_cell_name=sample_lane_metrics.flow_cell_name,
        flow_cell_lane_number=sample_lane_metrics.lane,
        sample_internal_id=sample_lane_metrics.sample_id,
        sample_total_reads_in_lane=sample_lane_metrics.total_reads,
        sample_base_percentage_passing_q30=sample_base_percentage_passing_q30,
        sample_base_mean_quality_score=sample_base_mean_quality_score,
        created_at=datetime.now(),
    )
