import logging
from datetime import datetime
from pathlib import Path
from typing import List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import Bcl2FastqSampleLaneMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import parse_bcl2fastq_sequencing_metrics
from cg.apps.sequencing_metrics_parser.sequencing_metrics_calculator import (
    calculate_average_quality_score,
    calculate_q30_bases_percentage,
)
from cg.store.models import SampleLaneSequencingMetrics

LOG = logging.getLogger(__name__)


def create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell(
    flow_cell_dir: Path,
) -> List[SampleLaneSequencingMetrics]:
    """
    Parses the Bcl2fastq generated stats.json files and aggregates and calculates metrics for each sample in each lane.

    Args:
        flow_cell_dir (Path): Demultiplexed flow cell directory containing output from bcl2fastq

    Returns:
        List[SampleLaneSequencingMetrics]: A list of SampleLaneSequencingMetrics representing the sequencing
        metrics for each sample in each lane on the flow cell.
    """

    sample_lane_sequencing_metrics: List[SampleLaneSequencingMetrics] = []
    LOG.debug(f"Parsing Bcl2fastq sequencing metrics for flow cell {flow_cell_dir}")
    sample_and_lane_metrics: List[Bcl2FastqSampleLaneMetrics] = parse_bcl2fastq_sequencing_metrics(
        flow_cell_dir=flow_cell_dir
    )
    LOG.debug(f"List to check is: {sample_lane_sequencing_metrics}")
    for raw_sample_metrics in sample_and_lane_metrics:
        LOG.debug(f"Creating SampleLaneSequencingMetrics for sample {raw_sample_metrics.sample_id}")
        metrics: SampleLaneSequencingMetrics = create_sample_lane_sequencing_metrics_from_bcl2fastq(
            bcl2fastq_sample_metrics=raw_sample_metrics
        )
        sample_lane_sequencing_metrics.append(metrics)

    return sample_lane_sequencing_metrics


def create_sample_lane_sequencing_metrics_from_bcl2fastq(
    bcl2fastq_sample_metrics: Bcl2FastqSampleLaneMetrics,
) -> SampleLaneSequencingMetrics:
    """
    Generates a SampleLaneSequencingMetrics based on the provided raw results.

    Args:
        raw_sample_metrics: Bcl2FastqSampleLaneMetrics: The raw sequencing metrics for a sample in a lane.

    Returns:
        SampleLaneSequencingMetrics: SampleLaneSequencingMetrics encapsulates the statistics for a sample
        in a lane on the flow cell.
    """

    sample_base_percentage_passing_q30: float = calculate_q30_bases_percentage(
        q30_yield=bcl2fastq_sample_metrics.sample_total_yield_q30_in_lane,
        total_yield=bcl2fastq_sample_metrics.sample_total_yield_in_lane,
    )
    sample_base_mean_quality_score: float = calculate_average_quality_score(
        total_quality_score=bcl2fastq_sample_metrics.sample_total_quality_score_in_lane,
        total_yield=bcl2fastq_sample_metrics.sample_total_yield_in_lane,
    )

    return SampleLaneSequencingMetrics(
        flow_cell_name=bcl2fastq_sample_metrics.flow_cell_name,
        flow_cell_lane_number=bcl2fastq_sample_metrics.flow_cell_lane_number,
        sample_internal_id=bcl2fastq_sample_metrics.sample_id,
        sample_total_reads_in_lane=bcl2fastq_sample_metrics.sample_total_reads_in_lane,
        sample_base_percentage_passing_q30=sample_base_percentage_passing_q30,
        sample_base_mean_quality_score=sample_base_mean_quality_score,
        created_at=datetime.now(),
    )
