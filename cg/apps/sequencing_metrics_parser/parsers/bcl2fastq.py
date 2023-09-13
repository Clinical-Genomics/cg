import logging
import os
from pathlib import Path
from typing import Iterable, List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    ReadMetric,
    SampleLaneMetrics,
    SampleLaneTileMetrics,
)
from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)

LOG = logging.getLogger(__name__)


def parse_bcl2fastq_sequencing_metrics(flow_cell_dir: Path) -> List[SampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: List[SampleLaneTileMetrics] = parse_raw_tile_metrics(flow_cell_dir)
    return aggregate_tile_metrics_per_sample_and_lane(tile_metrics)


def parse_raw_tile_metrics(
    demultiplex_result_directory: Path,
) -> List[SampleLaneTileMetrics]:
    """Parse metrics for each tile on a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: List[SampleLaneTileMetrics] = []

    stats_json_paths: List[Path] = get_bcl2fastq_stats_paths(demultiplex_result_directory)

    for stats_json_path in stats_json_paths:
        LOG.debug(f"Parsing stats.json file {stats_json_path}")
        metrics = SampleLaneTileMetrics.parse_file(stats_json_path)
        tile_metrics.append(metrics)

    return tile_metrics


def aggregate_tile_metrics_per_sample_and_lane(
    tile_metrics: List[SampleLaneTileMetrics],
) -> List[SampleLaneMetrics]:
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
                    metrics[sample_lane_key] = create_default_sample_lane_metrics(
                        flow_cell_name=tile_metric.flow_cell_name,
                        lane_number=conversion_result.lane_number,
                        sample_id=sample_id,
                    )

                read_metrics: List[ReadMetric] = demux_result.read_metrics
                metric: SampleLaneMetrics = metrics[sample_lane_key]

                # Double the total reads since they are reported in pairs
                metric.total_reads += demux_result.number_reads * 2
                metric.total_yield += demux_result.yield_
                metric.total_yield_q30 += calculate_q30_yield_sum(read_metrics)
                metric.total_quality_score += calculate_quality_score_sum(read_metrics)

    return list(metrics.values())


def discard_index_sequence(sample_id_with_index: str) -> str:
    """Discard the index sequence from the sample id."""
    return sample_id_with_index.split("_")[0]


def get_bcl2fastq_stats_paths(demultiplex_result_directory: Path) -> List[Path]:
    """
    Finds metrics files in Bcl2fastq demultiplex result directory.
    Raises:
        FileNotFoundError: If no stats.json files are found in the demultiplex result directory.
    """
    stats_json_paths = []

    for root, _, files in os.walk(demultiplex_result_directory):
        if root.endswith(BCL2FASTQ_METRICS_DIRECTORY_NAME) and BCL2FASTQ_METRICS_FILE_NAME in files:
            stats_json_paths.append(Path(root, BCL2FASTQ_METRICS_FILE_NAME))

    if not stats_json_paths:
        raise FileNotFoundError(
            f"Could not find any stats.json files in {demultiplex_result_directory}"
        )

    return stats_json_paths


def create_default_sample_lane_metrics(
    flow_cell_name: str, lane_number: int, sample_id: str
) -> SampleLaneMetrics:
    return SampleLaneMetrics(
        flow_cell_name=flow_cell_name,
        lane_number=lane_number,
        sample_id=sample_id,
        total_reads=0,
        total_yield=0,
        total_yield_q30=0,
        total_quality_score=0,
    )


def calculate_quality_score_sum(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.quality_score_sum for read_metric in read_metrics])


def calculate_q30_yield_sum(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.yield_q30 for read_metric in read_metrics])


def aggregate_undetermined_tile_metrics_per_lane(
    tile_metrics: List[SampleLaneTileMetrics],
) -> List[SampleLaneMetrics]:
    """Aggregate the undetermined tile metrics per lane instead."""
    metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            if conversion_result.undetermined is None:
                continue

            lane: int = conversion_result.lane_number
            flow_cell_name: str = tile_metric.flow_cell_name

            if lane not in metrics:
                metrics[lane] = create_default_sample_lane_metrics(
                    flow_cell_name=flow_cell_name,
                    lane_number=lane,
                    sample_id="undetermined",
                )

            metric: SampleLaneMetrics = metrics[lane]
            read_metrics: List[ReadMetric] = conversion_result.undetermined.read_metrics
            reads: int = conversion_result.undetermined.number_reads
            total_yield: int = conversion_result.undetermined.yield_

            metric.total_reads += reads * 2
            metric.total_yield += total_yield
            metric.total_yield_q30 += calculate_q30_yield_sum(read_metrics)
            metric.total_quality_score += calculate_quality_score_sum(read_metrics)


def parse_undetermined_metrics(flow_cell_dir: Path) -> List[SampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: List[SampleLaneTileMetrics] = parse_raw_tile_metrics(flow_cell_dir)
