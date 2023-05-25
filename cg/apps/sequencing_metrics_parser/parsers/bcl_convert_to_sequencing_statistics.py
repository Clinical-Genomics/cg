"""Module to parse the BCL convert metrics data into the sequencing statistics model."""

from pathlib import Path
from typing import List
from cg.store.models import SequencingStatistics
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from datetime import datetime
from cg.constants.demultiplexing import DRAGEN_PASSED_FILTER_PCT


def create_sequencing_statistics_from_bcl_convert_metrics(
    bcl_convert_metrics_dir_path: Path,
) -> List[SequencingStatistics]:
    """Parse the BCL convert metrics data into the sequencing statistics model."""
    metrics_parser: BclConvertMetricsParser = BclConvertMetricsParser(
        bcl_convert_metrics_dir_path=bcl_convert_metrics_dir_path,
    )
    sample_internal_ids: List[str] = metrics_parser.get_sample_internal_ids()
    sequencing_statistics: List[SequencingStatistics] = []
    for sample_internal_id in sample_internal_ids:
        for lane in metrics_parser.get_lanes_for_sample_internal_id(
            sample_internal_id=sample_internal_id
        ):
            sequencing_statistics.append(
                SequencingStatistics(
                    sample_internal_id=sample_internal_id,
                    flow_cell_name=metrics_parser.get_flow_cell_name(),
                    lane=lane,
                    yield_in_megabases=metrics_parser.calculate_total_yield_per_lane_in_mega_bases(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    read_counts=metrics_parser.calculate_total_reads_per_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    passed_filter_percent=DRAGEN_PASSED_FILTER_PCT,
                    raw_clusters_per_lane_percent=0,
                    perfect_index_reads_percent=metrics_parser.get_perfect_index_reads_percent_for_sample_per_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    bases_with_q30_percent=metrics_parser.get_q30_bases_percent_per_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    lanes_mean_quality_score=metrics_parser.get_mean_quality_score_per_lane(
                        sample_internal_id=sample_internal_id, lane=lane
                    ),
                    started_at=datetime.now(),
                )
            )

    return sequencing_statistics
