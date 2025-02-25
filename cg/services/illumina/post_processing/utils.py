"""Utility functions for the Illumina post-processing service."""

import logging
import re
from pathlib import Path

from cg.constants.constants import FileExtensions
from cg.constants.demultiplexing import DemultiplexingDirsAndFiles
from cg.constants.sequencing import FLOWCELL_Q30_THRESHOLD, Sequencers
from cg.services.illumina.data_transfer.models import (
    IlluminaSampleSequencingMetricsDTO,
)
from cg.utils.files import get_files_matching_pattern, is_pattern_in_file_path_name, rename_file

LOG = logging.getLogger(__name__)


def is_sample_negative_control_with_reads_in_lane(
    is_negative_control: bool, metric: IlluminaSampleSequencingMetricsDTO
) -> bool:
    return is_negative_control and metric.total_reads_in_lane != 0


def _is_sample_id_in_directory_name(directory: Path, sample_internal_id: str) -> bool:
    """Validate that directory name is formatted as Sample_<sample_id> or Sample_<sample_id>_."""
    sample_pattern: str = f"Sample_{sample_internal_id}"
    return f"{sample_pattern}_" in directory.name or sample_pattern == directory.name


def _is_file_path_compressed_fastq(file_path: Path) -> bool:
    return file_path.name.endswith(f"{FileExtensions.FASTQ}{FileExtensions.GZIP}")


def _is_lane_in_fastq_file_name(sample_fastq: Path) -> bool:
    """Validate that fastq contains lane number formatted as _L<lane_number>"""
    return bool(re.search(r"_L\d+", sample_fastq.name))


def _is_valid_sample_fastq_file(sample_fastq: Path, sample_internal_id: str) -> bool:
    """
    Validate that the sample fastq file name is formatted as expected.

    Assumptions:
    1. The sample fastq file name ends with .fastq.gz
    2. The sample fastq file name contains the lane number formatted as _L<lane_number>
    3. The sample internal id is present in the parent directory name or in the file name.
    """
    is_sample_id_in_directory: bool = _is_sample_id_in_directory_name(
        directory=sample_fastq.parent, sample_internal_id=sample_internal_id
    )
    is_sample_id_in_file_name: bool = is_pattern_in_file_path_name(
        file_path=sample_fastq, pattern=sample_internal_id
    )

    return (
        _is_file_path_compressed_fastq(sample_fastq)
        and _is_lane_in_fastq_file_name(sample_fastq)
        and (is_sample_id_in_directory or is_sample_id_in_file_name)
    )


def _get_valid_sample_fastqs(fastq_paths: list[Path], sample_internal_id: str) -> list[Path]:
    """Return a list of valid fastq files."""
    return [
        fastq
        for fastq in fastq_paths
        if _is_valid_sample_fastq_file(sample_fastq=fastq, sample_internal_id=sample_internal_id)
    ]


def get_sample_fastqs_from_flow_cell(
    demultiplexed_run_path: Path, sample_internal_id: str
) -> list[Path] | None:
    """Retrieve all fastq files for a specific sample in a demultiplex run directory."""

    # The flat output structure for runs demultiplexed with BCLConvert on hasta
    root_pattern = f"{sample_internal_id}_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"

    # The pattern for NovaSeqX flow cells demultiplexed on board of the dragen
    demux_on_sequencer_pattern = (
        f"BCLConvert/fastq/{sample_internal_id}"
        f"_S*_L*_R*_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    )

    for pattern in [
        root_pattern,
        demux_on_sequencer_pattern,
    ]:
        sample_fastqs: list[Path] = get_files_matching_pattern(
            directory=demultiplexed_run_path, pattern=pattern
        )
        valid_sample_fastqs: list[Path] = _get_valid_sample_fastqs(
            fastq_paths=sample_fastqs, sample_internal_id=sample_internal_id
        )

        if valid_sample_fastqs:
            return valid_sample_fastqs


def _add_flow_cell_name_to_fastq_file_path(fastq_file_path: Path, flow_cell_id: str) -> Path:
    """Add the flow cell name to the fastq file path if missing."""
    if is_pattern_in_file_path_name(file_path=fastq_file_path, pattern=flow_cell_id):
        LOG.debug(f"Flow cell id {flow_cell_id} already in {fastq_file_path}. Skipping renaming.")
        return fastq_file_path
    LOG.debug(f"Adding flow cell id {flow_cell_id} to {fastq_file_path}.")
    return Path(fastq_file_path.parent, f"{flow_cell_id}_{fastq_file_path.name}")


def rename_fastq_file_if_needed(fastq_file_path: Path, flow_cell_name: str) -> Path:
    """Rename the given fastq file path if the renamed fastq file path does not exist."""
    renamed_fastq_file_path: Path = _add_flow_cell_name_to_fastq_file_path(
        fastq_file_path=fastq_file_path, flow_cell_id=flow_cell_name
    )
    if fastq_file_path != renamed_fastq_file_path:
        rename_file(file_path=fastq_file_path, renamed_file_path=renamed_fastq_file_path)
    return renamed_fastq_file_path


def _get_weighted_average(
    total_1: int, percentage_1: float, total_2: int, percentage_2: float
) -> float:
    """Calculate the weighted average of two percentages."""
    if total_1 == 0 and total_2 == 0:
        return 0
    return (total_1 * percentage_1 + total_2 * percentage_2) / (total_1 + total_2)


def _combine_metrics(
    existing_metric: IlluminaSampleSequencingMetricsDTO,
    new_metric: IlluminaSampleSequencingMetricsDTO,
) -> IlluminaSampleSequencingMetricsDTO:
    """Update an existing metric with data from a new metric."""

    combined_q30_percentage: float = _get_weighted_average(
        total_1=existing_metric.total_reads_in_lane,
        percentage_1=existing_metric.base_passing_q30_percent,
        total_2=new_metric.total_reads_in_lane,
        percentage_2=new_metric.base_passing_q30_percent,
    )
    combined_mean_quality_score: float = _get_weighted_average(
        total_1=existing_metric.total_reads_in_lane,
        percentage_1=existing_metric.base_mean_quality_score,
        total_2=new_metric.total_reads_in_lane,
        percentage_2=new_metric.base_mean_quality_score,
    )
    combined_yield_q30_percentage: float = _get_weighted_average(
        total_1=existing_metric.yield_,
        percentage_1=existing_metric.yield_q30,
        total_2=new_metric.yield_,
        percentage_2=new_metric.yield_q30,
    )
    combined_reads: int = existing_metric.total_reads_in_lane + new_metric.total_reads_in_lane
    combined_yield: int = existing_metric.yield_ + new_metric.yield_

    existing_metric.base_passing_q30_percent = combined_q30_percentage
    existing_metric.base_mean_quality_score = combined_mean_quality_score
    existing_metric.total_reads_in_lane = combined_reads
    existing_metric.yield_ = combined_yield
    existing_metric.yield_q30 = combined_yield_q30_percentage

    return existing_metric


def combine_sample_metrics_with_undetermined(
    sample_metrics: list[IlluminaSampleSequencingMetricsDTO],
    undetermined_metrics: list[IlluminaSampleSequencingMetricsDTO],
) -> list[IlluminaSampleSequencingMetricsDTO]:
    """Combine metrics for sample metrics with metrics for undetermined reads.
    This occurs only if a sample is the only sample in a lane.
    """

    metrics: dict[tuple[str, int], IlluminaSampleSequencingMetricsDTO] = {
        (metric.sample_id, metric.flow_cell_lane): metric for metric in sample_metrics
    }
    for undetermined_metric in undetermined_metrics:
        key = (
            undetermined_metric.sample_id,
            undetermined_metric.flow_cell_lane,
        )
        existing_metric: IlluminaSampleSequencingMetricsDTO = metrics.get(key)

        if existing_metric:
            combined_metric: IlluminaSampleSequencingMetricsDTO = _combine_metrics(
                existing_metric=existing_metric, new_metric=undetermined_metric
            )
            metrics[key] = combined_metric
        else:
            metrics[key] = undetermined_metric
    return list(metrics.values())


def get_undetermined_fastqs(lane: int, demultiplexed_run_path: Path) -> list[Path]:
    """Get the undetermined fastq files for a specific lane on a flow cell."""
    undetermined_pattern = f"Undetermined*_L00{lane}_*{FileExtensions.FASTQ}{FileExtensions.GZIP}"
    undetermined_in_root: list[Path] = get_files_matching_pattern(
        directory=demultiplexed_run_path,
        pattern=undetermined_pattern,
    )
    return undetermined_in_root


def create_delivery_file_in_flow_cell_directory(flow_cell_directory: Path) -> None:
    Path(flow_cell_directory, DemultiplexingDirsAndFiles.DELIVERY).touch()


def get_lane_from_sample_fastq(sample_fastq_path: Path) -> int:
    """
    Extract the lane number from the sample fastq path.
    Pre-condition:
        - The fastq file name contains the lane number formatted as _L<lane_number>
    """
    pattern = r"_L(\d+)"
    lane_match = re.search(pattern, sample_fastq_path.name)

    if lane_match:
        return int(lane_match.group(1))

    raise ValueError(f"Could not extract lane number from fastq file name {sample_fastq_path.name}")


def get_q30_threshold(sequencer_type: Sequencers) -> int:
    return FLOWCELL_Q30_THRESHOLD[sequencer_type]
