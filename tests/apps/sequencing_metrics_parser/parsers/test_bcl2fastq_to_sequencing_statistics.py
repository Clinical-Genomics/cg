from typing import List
from pathlib import Path


from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    create_undetermined_sequencing_metrics_for_bcl2fastq_flow_cell,
)
from cg.store.models import SampleLaneSequencingMetrics


def test_create_sequencing_statistics_from_bcl2fastq_flow_cell(bcl2fastq_flow_cell_path: Path):
    """Test creating metrics for undetermined reads on a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a flow cell demultiplexed with bcl2fastq

    # WHEN creating undetermined metrics for an existing lane on the flow cell
    metrics: List[
        SampleLaneSequencingMetrics
    ] = create_undetermined_sequencing_metrics_for_bcl2fastq_flow_cell(
        flow_cell_dir=bcl2fastq_flow_cell_path, non_pooled_samples_and_lanes=[(1, "sample_id")]
    )

    # THEN a list of metrics is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneSequencingMetrics) for item in metrics)

    # THEN the metrics has been assigned the correct sample id
    assert metrics[0].sample_internal_id == "sample_id"


def test_create_undetermined_metrics_for_invalid_lane(bcl2fastq_flow_cell_path: Path):
    """Test creating metrics for undetrmined reads on a flow cell demultiplexed with bcl2fastq with an invalid lane."""
    # GIVEN a flow cell demultiplexed with bcl2fastq

    # WHEN creating metrics for a non existing lane on the flow cell
    metrics: List[
        SampleLaneSequencingMetrics
    ] = create_undetermined_sequencing_metrics_for_bcl2fastq_flow_cell(
        flow_cell_dir=bcl2fastq_flow_cell_path, non_pooled_samples_and_lanes=[(2, "sample_id")]
    )

    # THEN no metrics are returned
    assert not metrics
