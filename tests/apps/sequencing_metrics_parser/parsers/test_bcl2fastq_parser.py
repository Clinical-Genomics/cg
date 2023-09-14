from typing import Dict, List
import pytest
from pathlib import Path
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    SampleLaneMetrics,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import (
    parse_bcl2fastq_sequencing_metrics,
    parse_undetermined_metrics,
)


def test_parse_valid_bcl2fastq_sequencing_metrics(bcl2fastq_flow_cell_path: Path):
    """Test parsing metrics for a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a valid directory structure with a valid stats.json file

    # WHEN parsing the directory containing the valid stats.json file
    metrics: List[SampleLaneMetrics] = parse_bcl2fastq_sequencing_metrics(bcl2fastq_flow_cell_path)

    # THEN a list of Bcl2FastqTileSequencingMetrics models is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneMetrics) for item in metrics)


def test_parse_not_found_bcl2fastq_sequencing_metrics():
    """Test that an error is raised when the expected directory structure is not found."""
    # GIVEN a directory structure that does not contain the expected directory structure
    # WHEN parsing the directory containing the valid stats.json file
    # THEN a FileNotFoundError is raised
    with pytest.raises(FileNotFoundError):
        parse_bcl2fastq_sequencing_metrics(flow_cell_dir=Path("/does/not/exist"))


def test_parse_undetermined_metrics(bcl2fastq_flow_cell_path: Path):
    """Test parsing undetermined reads for a flow cell demultiplexed with bcl2fastq."""
    # GIVEN a flow cell demultiplexed with bcl2fastq containing undetermined reads

    # WHEN parsing the undetermined metrics
    metrics: List[SampleLaneMetrics] = parse_undetermined_metrics(bcl2fastq_flow_cell_path)

    # THEN a list of Bcl2FastqTileSequencingMetrics models is returned
    assert isinstance(metrics, list)
    assert all(isinstance(item, SampleLaneMetrics) for item in metrics)
