from pathlib import Path
from typing import List
from cg.store.api.core import Store
from cg.store.models import SampleLaneSequencingMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    get_sequencing_metrics_from_bcl2fastq,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert_to_sequencing_statistics import (
    create_sample_lane_sequencing_metrics_from_bcl_convert_metrics,
)


def create_sample_lane_sequencing_metrics(demultiplex_result_directory: Path, bcl_converter: str):
    """Check demultiplexing software:
    - call correct parser
    - return the sample lane sequencing metrics objects
    """
    metrics: List[SampleLaneSequencingMetrics] = []

    if bcl_converter == "bcl_convert":
        metrics: List[
            SampleLaneSequencingMetrics
        ] = create_sample_lane_sequencing_metrics_from_bcl_convert_metrics(
            demultiplex_result_directory=demultiplex_result_directory
        )
    else:
        metrics: List[SampleLaneSequencingMetrics] = get_sequencing_metrics_from_bcl2fastq(
            demultiplex_result_directory=demultiplex_result_directory
        )

    return metrics
