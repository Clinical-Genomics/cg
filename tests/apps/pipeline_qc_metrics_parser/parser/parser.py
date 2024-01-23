"""Tests for the pipeline qc metrics parser."""
from pathlib import Path

from cg.apps.pipeline_qc_metrics_parser.parser import parse_pipeline_qc_metric_file
from cg.models.pipeline_qc_metrics.pipeline_qc_metrics import PipelineQCMetric


def test_parse_pipeline_qc_metrics_file(mip_dna_pipeline_qc_metrics_path: Path):
    """Test to parse a pipeline qc metrics JSON file."""

    # GIVEN a path to a pipeline qc metrics JSON file.

    # WHEN parsing the JSON file.
    parsed_data: PipelineQCMetric = parse_pipeline_qc_metric_file(mip_dna_pipeline_qc_metrics_path)

    # THEN a pipeline qc metric models is returned
    assert isinstance(parsed_data, PipelineQCMetric)
