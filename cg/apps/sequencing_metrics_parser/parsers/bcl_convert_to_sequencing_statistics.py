"""Module to parse the BCL convert metrics data into the sequencing statistics model."""

from pathlib import Path
from typing import List
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from datetime import datetime
from cg.constants.demultiplexing import DRAGEN_PASSED_FILTER_PCT


def create_sample_lane_sequencing_metrics_from_bcl_convert_metrics(
    bcl_convert_metrics_dir_path: Path,
) -> List[SampleLaneSequencingMetrics]:
    """Parse the BCL convert metrics data into the sequencing statistics model."""
    metrics_parser: BclConvertMetricsParser = BclConvertMetricsParser(
        bcl_convert_metrics_dir_path=bcl_convert_metrics_dir_path,
    )
    sample_internal_ids: List[str] = metrics_parser.get_sample_internal_ids()
    sample_lane_sequencing_metrics: List[SampleLaneSequencingMetrics] = []
    for sample_internal_id in sample_internal_ids:
        for lane in metrics_parser.get_lanes_for_sample(sample_internal_id=sample_internal_id):
            sample_lane_sequencing_metrics.append(
                SampleLaneSequencingMetrics(
                    sample_internal_id=sample_internal_id,
                    flow_cell_name=metrics_parser.get_flow_cell_name(),
                    flow_cell_lane_number=lane,
                    sample_total_reads_in_lane=metrics_parser.calculate_total_reads_for_sample_in_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    sample_base_fraction_passing_q30=metrics_parser.get_q30_bases_percent_for_sample_in_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    sample_base_mean_quality_score=metrics_parser.get_mean_quality_score_for_sample_in_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    created_at=datetime.now(),
                )
            )

    return sample_lane_sequencing_metrics
