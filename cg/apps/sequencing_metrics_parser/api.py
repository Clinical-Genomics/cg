from pathlib import Path
from typing import List
from cg.constants.demultiplexing import BclConverter
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell,
)


def create_sample_lane_sequencing_metrics_for_flow_cell(
    flow_cell_directory: Path, bcl_converter: str
) -> List[SampleLaneSequencingMetrics]:
    """Parse the sequencing metrics data for the correct demultiplexing software into the sequencing statistics model."""
    if bcl_converter == BclConverter.BCLCONVERT:
        return create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell(
            flow_cell_dir=flow_cell_directory
        )
    return create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell(
        flow_cell_dir=flow_cell_directory
    )
