from pathlib import Path

from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq_to_sequencing_statistics import (
    create_bcl2fastq_undetermined_metrics,
)
from cg.store.models import SampleLaneSequencingMetrics


def test_create_sequencing_statistics_from_bcl2fastq_flow_cell(bcl2fastq_flow_cell_path: Path):
    """Test creating metrics for undetermined reads on a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a flow cell demultiplexed with bcl2fastq with one lane, one sample and two undetermined reads

    # WHEN creating undetermined metrics for the lane and sample
    metrics: list[SampleLaneSequencingMetrics] = create_bcl2fastq_undetermined_metrics(
        bcl2fastq_flow_cell_path=bcl2fastq_flow_cell_path,
        non_pooled_lane_sample_pairs=[(1, "sample_id")],
    )

    # THEN a list of metrics is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneSequencingMetrics) for item in metrics)
    assert len(metrics) == 1

    # THEN the undetermined metrics have been assigned the correct sample id and lane
    assert metrics[0].sample_internal_id == "sample_id"
    assert metrics[0].flow_cell_lane_number == 1

    # THEN the two undetermined paired reads in each tile were combined
    assert metrics[0].sample_total_reads_in_lane == 4


def test_create_undetermined_metrics_for_invalid_lane(bcl2fastq_flow_cell_path: Path):
    """Test creating metrics for undetrmined reads on a flow cell demultiplexed with bcl2fastq with an invalid lane."""
    # GIVEN a flow cell demultiplexed with bcl2fastq

    # WHEN creating metrics for a non existing lane on the flow cell
    metrics: list[SampleLaneSequencingMetrics] = create_bcl2fastq_undetermined_metrics(
        bcl2fastq_flow_cell_path=bcl2fastq_flow_cell_path,
        non_pooled_lane_sample_pairs=[(2, "sample_id")],
    )

    # THEN no metrics are returned
    assert not metrics
