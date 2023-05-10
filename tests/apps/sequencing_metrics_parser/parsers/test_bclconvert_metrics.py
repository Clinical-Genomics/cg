"""This module contains tests for the BCLConvert metrics parser."""
from pathlib import Path
from cg.apps.sequencing_metrics_parser.parsers.bclconvert_metrics import (
    read_bclconvert_metric_file_to_dict,
)


def test_read_bclconvert_metric_file_to_dict(bcl_convert_metric_file_path: Path):
    """Test to read the BCLconvert demultiplexing stats file into a dictionary."""

    # GIVEN a path to a BCLConvert metrics file

    # WHEN reading the file into a dictionary
    parsed_stats = read_bclconvert_metric_file_to_dict(bcl_convert_metric_file_path)

    # THEN assert that the dictionary is not empty
    assert parsed_stats
