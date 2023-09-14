from pathlib import Path
from typing import List, Tuple
from cg.constants.demultiplexing import BclConverter
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    create_bcl2fastq_metrics,
    create_bcl2fastq_undetermined_metrics,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell,
)


def create_sample_lane_sequencing_metrics_for_flow_cell(
    flow_cell_directory: Path, bcl_converter: str
) -> List[SampleLaneSequencingMetrics]:
    """Parse the sequencing metrics data for the correct demultiplexing software into the sequencing statistics model."""
    if bcl_converter == BclConverter.BCLCONVERT or bcl_converter == BclConverter.DRAGEN:
        return create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell(
            flow_cell_directory
        )
    return create_bcl2fastq_metrics(flow_cell_directory)


def create_undetermined_sequencing_metrics_for_flow_cell(
    flow_cell_directory: Path,
    bcl_converter: str,
    non_pooled_lanes_and_samples: List[Tuple[int, str]],
) -> List[SampleLaneSequencingMetrics]:
    """Return sequencing metrics for undetermined reads in the specified non-pooled lanes."""

    if bcl_converter == BclConverter.BCL2FASTQ:
        return create_bcl2fastq_undetermined_metrics(
            bcl2fastq_flow_cell_path=flow_cell_directory,
            non_pooled_lane_sample_pairs=non_pooled_lanes_and_samples,
        )
