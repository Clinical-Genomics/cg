"""This module contains tests for the BCLConvert metrics parser."""
from pathlib import Path

from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser


def test_parse_bcl_convert_metrics(
    bcl_convert_quality_metric_file_path,
    bcl_convert_demux_metric_file_path,
    bcl_convert_sample_sheet_file_path,
    bcl_convert_adapter_metrics_file_path,
    bcl_convert_run_info_file_path,
    bcl_convert_adapter_metric_model_with_data,
    bcl_convert_demux_metric_model_with_data,
    bcl_convert_quality_metric_model_with_data,
    bcl_convert_sample_sheet_model_with_data,
):
    """Test to parse BCLConvert metrics."""
    # GIVEN paths to a BCLConvert metrics files
    # WHEN parsing the files
    bcl_convert_metrics_parser = BclConvertMetricsParser(
        bcl_convert_quality_metrics_path=bcl_convert_quality_metric_file_path,
        bcl_convert_demux_metrics_file_path=bcl_convert_demux_metric_file_path,
        bcl_convert_sample_sheet_file_path=bcl_convert_sample_sheet_file_path,
        bcl_convert_adapter_metrics_file_path=bcl_convert_adapter_metrics_file_path,
        bcl_convert_run_info_file_path=bcl_convert_run_info_file_path,
    )

    # THEN assert that the metrics are parsed
    assert bcl_convert_metrics_parser.quality_metrics
    assert bcl_convert_metrics_parser.demux_metrics
    assert bcl_convert_metrics_parser.sample_sheet
    assert bcl_convert_metrics_parser.adapter_metrics
    assert bcl_convert_metrics_parser.run_info
