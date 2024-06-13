from pathlib import Path

from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser


def test_parse_valid_quality_metrics(report_path_qc_pass: Path):
    # GIVEN a valid quality metrics file path

    # WHEN parsing the file
    MetricsParser.parse_samples_results(report_path_qc_pass)

    # THEN no error is thrown
