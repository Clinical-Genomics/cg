import os
from pathlib import Path
import re
from typing import List
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    Bcl2FastqTileSequencingMetrics,
)


def parse_bcl2fastq_tile_sequencing_metrics(
    demultiplex_result_directory: Path,
) -> List[Bcl2FastqTileSequencingMetrics]:
    """
    Parse stats.json files in specified Bcl2fastq demultiplex result directory.

    This function navigates through subdirectories in the given path, identifies
    and parses the Stats.json files from Bcl2fastq specifying metrics per sample, lane and tile
    on the flow cell and returns a list of parsed sequencing metrics resolved per tile.

    Parameters:
    demultiplex_result_directory (Path): Path to the demultiplexing results.

    Returns:
    List[Bcl2FastqTileSequencingMetrics]: List of parsed sequencing metrics per tile.
    """
    tile_sequencing_metrics = []

    stats_json_paths: List[Path] = get_bcl2fastq_stats_paths(
        demultiplex_result_directory=demultiplex_result_directory
    )

    for stats_json_path in stats_json_paths:
        sequencing_metrics = Bcl2FastqTileSequencingMetrics.parse_file(stats_json_path)
        tile_sequencing_metrics.append(sequencing_metrics)

    return tile_sequencing_metrics


def get_bcl2fastq_stats_paths(demultiplex_result_directory: Path) -> List[Path]:
    """
    Identify and return paths to stats.json files in Bcl2fastq demultiplex result directory.

    This function looks through subdirectories in the given demultiplex directory,
    matching specific naming pattern (l<num>t<num>), and collects paths
    to any stats.json files found within a "Stats" subdirectory.

    Parameters:
    demultiplex_result_directory (Path): Path to the demultiplexing results.

    Returns:
    List[Path]: List of paths to identified stats.json files.
    """
    stats_json_paths = []
    pattern = re.compile(r"l\d+t\d+")

    for subdir in os.listdir(demultiplex_result_directory):
        if pattern.match(subdir):
            stats_json_path = Path(demultiplex_result_directory, subdir, "Stats", "Stats.json")
            if stats_json_path.is_file():
                stats_json_paths.append(stats_json_path)

    return stats_json_paths
