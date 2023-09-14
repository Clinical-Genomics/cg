import logging
import os
from pathlib import Path
from typing import Iterable, List

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    DemuxResult,
    ReadMetric,
    SampleLaneMetrics,
    SampleLaneTileMetrics,
    Undetermined,
)
from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)

LOG = logging.getLogger(__name__)


def parse_bcl2fastq_sequencing_metrics(flow_cell_dir: Path) -> List[SampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: List[SampleLaneTileMetrics] = parse_raw_tile_metrics(flow_cell_dir)
    return combine_tile_metrics_per_sample_and_lane(tile_metrics)


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


def update_lane_metrics_with_demux_data(
    sample_lane_metrics: SampleLaneMetrics, demux_result: DemuxResult
):
    reads: int = demux_result.number_reads
    sample_lane_metrics.total_reads += reads * 2

    yield_: int = demux_result.yield_
    sample_lane_metrics.total_yield += yield_

    read_metrics: List[ReadMetric] = demux_result.read_metrics
    sample_lane_metrics.total_yield_q30 += sum_q30_yields(read_metrics)
    sample_lane_metrics.total_quality_score += sum_quality_scores(read_metrics)


def combine_tile_metrics_per_sample_and_lane(
    tile_metrics: List[SampleLaneTileMetrics],
) -> List[SampleLaneMetrics]:
    """Aggregate the tile metrics per sample and lane."""
    metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            for demux_result in conversion_result.demux_results:
                sample_lane_key = (
                    conversion_result.lane_number,
                    demux_result.sample_id,
                )

                sample_id: str = remove_index_from_sample_id(
                    sample_id_with_index=demux_result.sample_id
                )

                if sample_lane_key not in metrics:
                    metrics[sample_lane_key] = create_default_sample_lane_metrics(
                        flow_cell_name=tile_metric.flow_cell_name,
                        lane=conversion_result.lane_number,
                        sample_id=sample_id,
                    )

                update_lane_metrics_with_demux_data(
                    sample_lane_metrics=metrics[sample_lane_key], demux_result=demux_result
                )

    return list(metrics.values())


def remove_index_from_sample_id(sample_id_with_index: str) -> str:
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
    flow_cell_name: str, lane: int, sample_id: str
) -> SampleLaneMetrics:
    return SampleLaneMetrics(
        flow_cell_name=flow_cell_name,
        lane=lane,
        sample_id=sample_id,
        total_reads=0,
        total_yield=0,
        total_yield_q30=0,
        total_quality_score=0,
    )


def sum_quality_scores(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.quality_score_sum for read_metric in read_metrics])


def sum_q30_yields(read_metrics: Iterable[ReadMetric]) -> int:
    return sum([read_metric.yield_q30 for read_metric in read_metrics])


def update_lane_metrics_with_undetermined_data(
    sample_lane_metric: SampleLaneMetrics, undetermined_data: Undetermined
):
    reads: int = undetermined_data.number_reads
    sample_lane_metric.total_reads += reads * 2

    yield_: int = undetermined_data.yield_
    sample_lane_metric.total_yield += yield_

    read_metrics: List[ReadMetric] = undetermined_data.read_metrics
    sample_lane_metric.total_yield_q30 += sum_q30_yields(read_metrics)
    sample_lane_metric.total_quality_score += sum_quality_scores(read_metrics)


def combine_undetermined_lane_metrics_from_tiles(
    tile_metrics: List[SampleLaneTileMetrics],
) -> List[SampleLaneMetrics]:
    """Aggregate the undetermined tile metrics per lane."""
    sample_lane_metrics = {}

    for tile_metric in tile_metrics:
        for conversion_result in tile_metric.conversion_results:
            if conversion_result.undetermined is None:
                continue

            lane: int = conversion_result.lane_number
            flow_cell_name: str = tile_metric.flow_cell_name

            if lane not in sample_lane_metrics:
                sample_lane_metrics[lane] = create_default_sample_lane_metrics(
                    flow_cell_name=flow_cell_name,
                    lane=lane,
                    sample_id="undetermined",
                )

            update_lane_metrics_with_undetermined_data(
                sample_lane_metric=sample_lane_metrics[lane],
                undetermined_data=conversion_result.undetermined,
            )
    return list(sample_lane_metrics.values())


def parse_undetermined_metrics(flow_cell_dir: Path) -> List[SampleLaneMetrics]:
    """Parse metrics for a flow cell demultiplexed with Bcl2fastq."""
    tile_metrics: List[SampleLaneTileMetrics] = parse_raw_tile_metrics(flow_cell_dir)
    return combine_undetermined_lane_metrics_from_tiles(tile_metrics)
