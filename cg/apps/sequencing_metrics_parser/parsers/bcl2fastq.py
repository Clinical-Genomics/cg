import os
import re
from pathlib import Path
from typing import List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    Bcl2FastqSampleLaneMetrics,
    Bcl2FastqSampleLaneTileMetrics,
)
from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)


def parse_bcl2fastq_sequencing_metrics(flow_cell_dir: Path) -> List[Bcl2FastqSampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_sequencing_metrics: List[
        Bcl2FastqSampleLaneTileMetrics
    ] = parse_bcl2fastq_raw_tile_metrics(flow_cell_dir)

    return aggregate_tile_metrics_per_sample_and_lane(tile_sequencing_metrics)


def parse_bcl2fastq_raw_tile_metrics(
    demultiplex_result_directory: Path,
) -> List[Bcl2FastqSampleLaneTileMetrics]:
    """Parse metrics for each tile on a flow cell demultiplexed with Bcl2fastq."""
    tile_sequencing_metrics: List[Bcl2FastqSampleLaneTileMetrics] = []

    stats_json_paths: List[Path] = get_bcl2fastq_stats_paths(
        demultiplex_result_directory=demultiplex_result_directory
    )

    for stats_json_path in stats_json_paths:
        if not stats_json_path.exists():
            raise FileNotFoundError(f"File {stats_json_path} does not exist.")
        sequencing_metrics = Bcl2FastqSampleLaneTileMetrics.parse_file(stats_json_path)
        tile_sequencing_metrics.append(sequencing_metrics)

    return tile_sequencing_metrics


def aggregate_tile_metrics_per_sample_and_lane(
    tile_metrics: List[Bcl2FastqSampleLaneTileMetrics],
) -> List[Bcl2FastqSampleLaneMetrics]:
    """Aggregate the tile metrics per sample and lane instead."""
    metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            for demux_result in conversion_result.demux_results:
                sample_lane_key = (
                    conversion_result.lane_number,
                    demux_result.sample_id,
                )

                sample_id: str = discard_index_sequence(sample_id_with_index=demux_result.sample_id)

                if sample_lane_key not in metrics:
                    metrics[sample_lane_key] = Bcl2FastqSampleLaneMetrics(
                        flow_cell_name=tile_metric.flow_cell_name,
                        flow_cell_lane_number=conversion_result.lane_number,
                        sample_id=sample_id,
                        sample_total_reads_in_lane=0,
                        sample_total_yield_in_lane=0,
                        sample_total_yield_q30_in_lane=0,
                        sample_total_quality_score_in_lane=0,
                    )
                # Double the total reads since they are reported in pairs
                metrics[sample_lane_key].sample_total_reads_in_lane += demux_result.number_reads * 2
                metrics[sample_lane_key].sample_total_yield_in_lane += demux_result.yield_
                metrics[sample_lane_key].sample_total_yield_q30_in_lane += sum(
                    [read_metric.yield_q30 for read_metric in demux_result.read_metrics]
                )
                metrics[sample_lane_key].sample_total_quality_score_in_lane += sum(
                    [read_metric.quality_score_sum for read_metric in demux_result.read_metrics]
                )

    return list(metrics.values())


def discard_index_sequence(sample_id_with_index: str) -> str:
    """Discard the index sequence from the sample id."""
    return sample_id_with_index.split("_")[0]


def get_bcl2fastq_stats_paths(demultiplex_result_directory: Path) -> List[Path]:
    """Find metrics files in Bcl2fastq demultiplex result directory."""
    stats_json_paths = []
    pattern = re.compile(r"l\d+t\d+")

    for subdir in os.listdir(demultiplex_result_directory):
        if pattern.match(subdir):
            stats_json_path = (
                demultiplex_result_directory
                / subdir
                / BCL2FASTQ_METRICS_DIRECTORY_NAME
                / BCL2FASTQ_METRICS_FILE_NAME
            )
            if stats_json_path.is_file():
                stats_json_paths.append(stats_json_path)

    return stats_json_paths
