"""Module to parse the BCL convert metrics data into the sequencing statistics model."""

from pathlib import Path
from typing import List
from cg.store.models import SequencingStatistics
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from datetime import datetime
from cg.constants.demultiplexing import DRAGEN_PASSED_FILTER_PCT


def get_metrics_from_bcl_convert_metrics_parser(
    adapter_metrics_file_path: Path,
    quality_metrics_file_path: Path,
    demux_metrics_file_path: Path,
    sample_sheet_file_path: Path,
    run_info_file_path: Path,
) -> List[SequencingStatistics]:
    """Parse the BCL convert metrics data into the sequencing statistics model."""
    metrics_parser: BclConvertMetricsParser = BclConvertMetricsParser(
        bcl_convert_adapter_metrics_file_path=adapter_metrics_file_path,
        bcl_convert_quality_metrics_file_path=quality_metrics_file_path,
        bcl_convert_demux_metrics_file_path=demux_metrics_file_path,
        bcl_convert_sample_sheet_file_path=sample_sheet_file_path,
        bcl_convert_run_info_file_path=run_info_file_path,
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
