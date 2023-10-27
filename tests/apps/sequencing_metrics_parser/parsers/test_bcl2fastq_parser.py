from pathlib import Path

import pytest

from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import SampleLaneMetrics
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import (
    parse_metrics,
    parse_undetermined_non_pooled_metrics,
)


def test_parse_valid_bcl2fastq_sequencing_metrics(bcl2fastq_flow_cell_path: Path):
    """Test parsing metrics for a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a flow cell demultiplexed with bcl2fastq

    # WHEN parsing the flow cell
    metrics: list[SampleLaneMetrics] = parse_metrics(bcl2fastq_flow_cell_path)

    # THEN a list of metrics is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneMetrics) for item in metrics)


def test_parse_invalid_bcl2fastq_sequencing_metrics(tmp_path: Path):
    """Test that an error is raised for an invalid flow cell."""
    # GIVEN an invalid bcl2fastq flow cell directory
    # WHEN parsing flow cell
    # THEN a FileNotFoundError is raised
    with pytest.raises(FileNotFoundError):
        parse_metrics(tmp_path)


def test_parse_undetermined_metrics(bcl2fastq_flow_cell_path: Path):
    """Test parsing undetermined reads for a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a flow cell demultiplexed with bcl2fastq containing undetermined reads

    # WHEN parsing the undetermined metrics for the flow cell
    metrics: list[SampleLaneMetrics] = parse_undetermined_non_pooled_metrics(
        flow_cell_dir=bcl2fastq_flow_cell_path, non_pooled_lane_sample_pairs=[(1, "sample_id")]
    )

    # THEN a list of metrics is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneMetrics) for item in metrics)

    # THEN the metrics has been assigned the correct sample id
    assert metrics[0].sample_id == "sample_id"
