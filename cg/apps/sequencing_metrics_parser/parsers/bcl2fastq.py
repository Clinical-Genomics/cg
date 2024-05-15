import logging
import os
from pathlib import Path
from typing import Iterable

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    ReadMetric,
    SampleLaneMetrics,
    SampleLaneTileMetrics,
    TileReads,
    UndeterminedTileReads,
)
from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)
from cg.io.json import read_json

LOG = logging.getLogger(__name__)


def scale_paired_reads_to_total_reads(paired_reads: int) -> int:
    """Multiply the read count of R1 by two to represent the total amount of reads for both read pairs R1 and R2."""
    return paired_reads * 2


def remove_index_from_sample_id(sample_id_with_index: str) -> str:
    return sample_id_with_index.split("_")[0]


def sum_quality_scores(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.read_quality_score_sum for read_metric in read_metrics])


def sum_q30_yields(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.read_yield_q30 for read_metric in read_metrics])


def get_metrics_file_paths(demultiplex_result_directory: Path) -> list[Path]:
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


def create_empty_lane_metric(flow_cell_name: str, lane: int, sample_id: str) -> SampleLaneMetrics:
    return SampleLaneMetrics(
        flow_cell_name=flow_cell_name,
        lane=lane,
        sample_id=sample_id,
        total_reads=0,
        total_yield=0,
        total_yield_q30=0,
        total_quality_score=0,
    )


def update_lane_metrics_with_tile_reads(lane_metrics: SampleLaneMetrics, tile_reads: TileReads):
    tile_sample_reads: int = tile_reads.tile_sample_reads
    lane_metrics.total_reads += scale_paired_reads_to_total_reads(tile_sample_reads)

    tile_yield: int = tile_reads.tile_sample_yield
    lane_metrics.total_yield += tile_yield

    read_metrics: list[ReadMetric] = tile_reads.tile_sample_read_metrics
    lane_metrics.total_yield_q30 += sum_q30_yields(read_metrics)
    lane_metrics.total_quality_score += sum_quality_scores(read_metrics)


def update_lane_metrics_with_undetermined_tile_data(
    lane_metrics: SampleLaneMetrics, undetermined_tile_metrics: UndeterminedTileReads
):
    tile_total_reads: int = undetermined_tile_metrics.tile_total_reads
    lane_metrics.total_reads += scale_paired_reads_to_total_reads(tile_total_reads)

    tile_total_yield: int = undetermined_tile_metrics.tile_total_yield
    lane_metrics.total_yield += tile_total_yield

    tile_read_metrics: list[ReadMetric] = undetermined_tile_metrics.tile_read_metrics
    lane_metrics.total_yield_q30 += sum_q30_yields(tile_read_metrics)
    lane_metrics.total_quality_score += sum_quality_scores(tile_read_metrics)


def combine_tiles_per_lane(tile_metrics: list[SampleLaneTileMetrics]) -> list[SampleLaneMetrics]:
    """Aggregate the tile metrics to per lane instead."""
    metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            for demux_result in conversion_result.tile_reads:
                metric_key = (
                    conversion_result.lane,
                    demux_result.sample_id,
                )
                sample_id: str = remove_index_from_sample_id(demux_result.sample_id)

                if metric_key not in metrics:
                    metrics[metric_key] = create_empty_lane_metric(
                        flow_cell_name=tile_metric.flow_cell_name,
                        lane=conversion_result.lane,
                        sample_id=sample_id,
                    )
                update_lane_metrics_with_tile_reads(
                    lane_metrics=metrics[metric_key], tile_reads=demux_result
                )
    return list(metrics.values())


def combine_undetermined_tiles_per_lane(
    tile_metrics: list[SampleLaneTileMetrics],
) -> dict[int, SampleLaneMetrics]:
    """Aggregate the undetermined tile metrics per lane."""
    lane_metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            if conversion_result.tile_undetermined_reads is None:
                continue

            lane: int = conversion_result.lane

            if lane not in lane_metrics:
                lane_metrics[lane] = create_empty_lane_metric(
                    flow_cell_name=tile_metric.flow_cell_name,
                    lane=lane,
                    sample_id="undetermined",
                )

            update_lane_metrics_with_undetermined_tile_data(
                lane_metrics=lane_metrics[lane],
                undetermined_tile_metrics=conversion_result.tile_undetermined_reads,
            )
    return lane_metrics


def get_metrics_for_non_pooled_samples(
    lane_metrics: dict[int, SampleLaneMetrics], non_pooled_lane_sample_pairs: list[tuple[int, str]]
) -> list[SampleLaneMetrics]:
    """Get metrics for non pooled samples and set sample ids."""
    non_pooled_metrics: list[SampleLaneMetrics] = []
    for lane, sample_id in non_pooled_lane_sample_pairs:
        metric: SampleLaneMetrics | None = lane_metrics.get(lane)
        if not metric:
            continue
        metric.sample_id = sample_id
        non_pooled_metrics.append(metric)
    return non_pooled_metrics


def parse_metrics(flow_cell_dir: Path) -> list[SampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: list[SampleLaneTileMetrics] = parse_tile_metrics(flow_cell_dir)
    return combine_tiles_per_lane(tile_metrics)


def parse_tile_metrics(
    demultiplex_result_directory: Path,
) -> list[SampleLaneTileMetrics]:
    """Parse metrics for each tile on a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: list[SampleLaneTileMetrics] = []

    stats_paths: list[Path] = get_metrics_file_paths(demultiplex_result_directory)

    for json_path in stats_paths:
        LOG.debug(f"Parsing stats.json file {json_path}")
        data = read_json(json_path)
        metrics = SampleLaneTileMetrics.model_validate(data)
        tile_metrics.append(metrics)

    return tile_metrics


def parse_undetermined_non_pooled_metrics(
    flow_cell_dir: Path, non_pooled_lane_sample_pairs: list[tuple[int, str]]
) -> list[SampleLaneMetrics]:
    """Parse undetermined metrics for a flow cell demultiplexed with Bcl2fastq for non pooled samples."""
    tile_metrics: list[SampleLaneTileMetrics] = parse_tile_metrics(flow_cell_dir)
    lane_metrics: dict[int, SampleLaneMetrics] = combine_undetermined_tiles_per_lane(tile_metrics)

    return get_metrics_for_non_pooled_samples(
        lane_metrics=lane_metrics, non_pooled_lane_sample_pairs=non_pooled_lane_sample_pairs
    )
