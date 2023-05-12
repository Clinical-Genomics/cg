"""This module contains tests for the BCLConvert metrics parser."""
from pathlib import Path
from cg.apps.sequencing_metrics_parser.parsers.bcl_convert.bclconvert_metrics import (
    read_metric_file_to_dict,
    read_bcl_convert_sample_sheet_file_to_dict,
    parse_bcl_convert_metrics_file,
    read_quality_metrics_file_to_dict,
    read_adapter_metrics_file_to_dict,
    read_run_info_file,
)


def test_read_bcl_convert_metric_file_to_dict(bcl_convert_demux_metric_file_path: Path):
    """Test to read the BCLconvert demultiplexing stats file into a dictionary."""

    # GIVEN a path to a BCLConvert metrics file

    # WHEN reading the file into a dictionary
    parsed_demux_metrics = read_metric_file_to_dict(bcl_convert_demux_metric_file_path)

    # THEN assert that the dictionary is not empty
    assert parsed_demux_metrics


def test_read_bcl_convert_quality_metrics_file_to_dict(bcl_convert_quality_metric_file_path: Path):
    """Test to read the BCLconvert quality metrics file into a dictionary."""

    # GIVEN a path to a BCLConvert quality metrics file

    # WHEN reading the file into a dictionary
    parsed_quality_metrics = read_quality_metrics_file_to_dict(bcl_convert_quality_metric_file_path)

    # THEN assert that the dictionary is not empty
    assert parsed_quality_metrics


def test_read_bcl_convert_sample_sheet_file_to_dict(bcl_convert_sample_sheet_file_path: Path):
    """Test to read the BCLconvert quality metrics file into a dictionary."""

    # GIVEN a path to a BCLConvert quality metrics file

    # WHEN reading the file into a dictionary
    parsed_quality_metrics = read_bcl_convert_sample_sheet_file_to_dict(
        bcl_convert_sample_sheet_file_path
    )

    # THEN assert that the dictionary is not empty
    assert parsed_quality_metrics


def test_parse_bcl_convert_metrics_file(
    bcl_convert_demux_metric_file_path: Path,
    bcl_convert_quality_metric_file_path: Path,
    bcl_convert_sample_sheet_file_path: Path,
):
    """Test to parse the BCLConvert metrics file."""

    # GIVEN a path to a BCLConvert metrics file

    # WHEN parsing the file
    parsed_metrics = parse_bcl_convert_metrics_file(
        bcl_convert_metrics_file_path=bcl_convert_demux_metric_file_path,
        bcl_convert_quality_metrics_path=bcl_convert_quality_metric_file_path,
        bcl_convert_sample_sheet_path=bcl_convert_sample_sheet_file_path,
    )

    # THEN assert that the dictionary is not empty
    assert parsed_metrics


def test_read_bcl_convert_adapter_metrics_file_to_dict(bcl_convert_adapter_metrics_file_path: Path):
    """Test to read the BCLconvert adapter metrics file into a dictionary."""

    # GIVEN a path to a BCLConvert adapter metrics file

    # WHEN reading the file into a dictionary
    parsed_adapter_metrics = read_adapter_metrics_file_to_dict(
        bcl_convert_adapter_metrics_file_path
    )

    # THEN assert that the dictionary is not empty
    assert parsed_adapter_metrics


def test_read_run_info_file(bcl_convert_run_info_file_path: Path):
    """Test to read the BCLconvert run info file into a dictionary."""

    # GIVEN a path to a BCLConvert run info file

    # WHEN reading the file into a dictionary
    parsed_run_info = read_run_info_file(bcl_convert_run_info_file_path)

    # THEN assert that the dictionary is not empty
    assert parsed_run_info
