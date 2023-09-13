import json

import pytest
from pathlib import Path
from cg.apps.sequencing_metrics_parser.models.bcl2fastq_metrics import (
    SampleLaneMetrics,
)
from cg.apps.sequencing_metrics_parser.parsers.bcl2fastq import (
    parse_bcl2fastq_sequencing_metrics,
)
from cg.constants.demultiplexing import (
    BCL2FASTQ_METRICS_DIRECTORY_NAME,
    BCL2FASTQ_METRICS_FILE_NAME,
)


def test_parse_valid_bcl2fastq_sequencing_metrics(tmp_path, valid_bcl2fastq_metrics_data):
    """Test that valid stats.json files as generated by bcl2fastq in the expected directory structure can be parsed correctly."""
    # GIVEN a valid directory structure with a valid stats.json file
    valid_dir = tmp_path / "l1t1" / BCL2FASTQ_METRICS_DIRECTORY_NAME
    valid_dir.mkdir(parents=True)
    stats_json_path = valid_dir / BCL2FASTQ_METRICS_FILE_NAME
    stats_json_path.write_text(json.dumps(valid_bcl2fastq_metrics_data))

    # WHEN parsing the directory containing the valid stats.json file
    result = parse_bcl2fastq_sequencing_metrics(flow_cell_dir=tmp_path)

    # THEN a list of Bcl2FastqTileSequencingMetrics models is returned
    assert isinstance(result, list)
    assert all(isinstance(item, SampleLaneMetrics) for item in result)

    # THEN the Bcl2FastqTileSequencingMetrics model contains the expected data
    assert result[0].flow_cell_name == valid_bcl2fastq_metrics_data["Flowcell"]


def test_parse_not_found_bcl2fastq_sequencing_metrics():
    """Test that an error is raised when the expected directory structure is not found."""
    # GIVEN a directory structure that does not contain the expected directory structure
    # WHEN parsing the directory containing the valid stats.json file
    # THEN a FileNotFoundError is raised
    with pytest.raises(FileNotFoundError):
        parse_bcl2fastq_sequencing_metrics(flow_cell_dir=Path("/does/not/exist"))
