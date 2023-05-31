from pathlib import Path
from typing import List
from cg.store.api.core import Store
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell,
)


def create_sample_lane_sequencing_metrics_for_flow_cell(flow_cell_dir: Path, bcl_converter: str):
    """Parse the sequencing metrics data for the correct demultiplexing software into the sequencing statistics model."""
    metrics: List[SampleLaneSequencingMetrics] = []
    if bcl_converter == "bcl_convert":
        metrics = create_sample_lane_sequencing_metrics_from_bcl_convert_metrics_for_flow_cell(
            demultiplex_result_directory=flow_cell_dir
        )
    else:
        metrics = create_sample_lane_sequencing_metrics_from_bcl2fastq_for_flow_cell(
            demultiplex_result_directory=flow_cell_dir
        )
    return metrics
