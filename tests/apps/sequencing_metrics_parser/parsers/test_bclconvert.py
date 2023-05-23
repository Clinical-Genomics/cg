"""This module contains tests for the BCLConvert metrics parser."""
from pathlib import Path

from cg.apps.sequencing_metrics_parser.parsers.bcl_convert import BclConvertMetricsParser
from cg.apps.sequencing_metrics_parser.models.bcl_convert import (
    BclConvertQualityMetrics,
    BclConvertDemuxMetrics,
    BclConvertSampleSheetData,
    BclConvertAdapterMetrics,
    BclConvertRunInfo,
)


def test_parse_bcl_convert_metrics(
    bcl_convert_quality_metric_file_path,
    bcl_convert_demux_metric_file_path,
    bcl_convert_sample_sheet_file_path,
    bcl_convert_adapter_metrics_file_path,
    bcl_convert_run_info_file_path,
):
    """Test to parse BCLConvert metrics."""
    # GIVEN paths to a BCLConvert metrics files
    # WHEN parsing the files
    bcl_convert_metrics_parser = BclConvertMetricsParser(
        bcl_convert_quality_metrics_file_path=bcl_convert_quality_metric_file_path,
        bcl_convert_demux_metrics_file_path=bcl_convert_demux_metric_file_path,
        bcl_convert_sample_sheet_file_path=bcl_convert_sample_sheet_file_path,
        bcl_convert_adapter_metrics_file_path=bcl_convert_adapter_metrics_file_path,
        bcl_convert_run_info_file_path=bcl_convert_run_info_file_path,
    )

    # THEN assert that the metrics are parsed
    assert bcl_convert_metrics_parser.quality_metrics
    assert isinstance(bcl_convert_metrics_parser.quality_metrics[0], BclConvertQualityMetrics)
    assert bcl_convert_metrics_parser.demux_metrics
    assert isinstance(bcl_convert_metrics_parser.demux_metrics[0], BclConvertDemuxMetrics)
    assert bcl_convert_metrics_parser.sample_sheet
    assert isinstance(bcl_convert_metrics_parser.sample_sheet[0], BclConvertSampleSheetData)
    assert bcl_convert_metrics_parser.adapter_metrics
    assert isinstance(bcl_convert_metrics_parser.adapter_metrics[0], BclConvertAdapterMetrics)
    assert bcl_convert_metrics_parser.run_info
    assert isinstance(bcl_convert_metrics_parser.run_info, BclConvertRunInfo)


def test_parse_bcl_convert_quality_metrics(
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
    bcl_convert_quality_metric_model_with_data: BclConvertQualityMetrics,
):
    """Test to parse BCLConvert quality metrics."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed quality metrics are correct
    quality_metrics_model: BclConvertQualityMetrics = parsed_bcl_convert_metrics.quality_metrics[0]

    # ASSERT that the parsed quality metrics are of the correct type
    assert isinstance(quality_metrics_model, BclConvertQualityMetrics)

    # ASSERT that the parsed quality metrics has the correct values
    for attr_name, attr_value in quality_metrics_model.dict().items():
        assert getattr(bcl_convert_quality_metric_model_with_data, attr_name) == attr_value


def test_parse_bcl_convert_adapter_metrics(
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
    bcl_convert_adapter_metric_model_with_data: BclConvertAdapterMetrics,
):
    """Test to parse BCLConvert adapter metrics."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed adapter metrics are correct
    adapter_metrics_model: BclConvertAdapterMetrics = parsed_bcl_convert_metrics.adapter_metrics[0]

    # ASSERT that the parsed adapter metrics are of the correct type
    assert isinstance(adapter_metrics_model, BclConvertAdapterMetrics)

    # ASSERT that the parsed adapter metrics has the correct values
    for attr_name, attr_value in adapter_metrics_model.dict().items():
        assert getattr(bcl_convert_adapter_metric_model_with_data, attr_name) == attr_value


def test_parse_bcl_convert_demux_metrics(
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
    bcl_convert_demux_metric_model_with_data: BclConvertDemuxMetrics,
):
    """Test to parse BCLConvert demux metrics."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed demux metrics are correct
    demux_metrics_model: BclConvertDemuxMetrics = parsed_bcl_convert_metrics.demux_metrics[0]

    # ASSERT that the parsed demux metrics are of the correct type
    assert isinstance(demux_metrics_model, BclConvertDemuxMetrics)

    # ASSERT that the parsed demux metrics has the correct values
    for attr_name, attr_value in demux_metrics_model.dict().items():
        assert getattr(bcl_convert_demux_metric_model_with_data, attr_name) == attr_value


def test_parse_bcl_convert_sample_sheet(
    parsed_bcl_convert_metrics: BclConvertMetricsParser,
    bcl_convert_sample_sheet_model_with_data: BclConvertSampleSheetData,
):
    """Test to parse BCLConvert sample sheet."""
    # GIVEN a parsed BCLConvert metrics

    # ASSERT that the parsed sample sheet is correct
    sample_sheet_model: BclConvertSampleSheetData = parsed_bcl_convert_metrics.sample_sheet[0]

    # ASSERT that the parsed sample sheet is of the correct type
    assert isinstance(sample_sheet_model, BclConvertSampleSheetData)

    # ASSERT that the parsed sample sheet has the correct values
    for attr_name, attr_value in sample_sheet_model.dict().items():
        assert getattr(bcl_convert_sample_sheet_model_with_data, attr_name) == attr_value
