from pathlib import Path

from cg.meta.workflow.mutant.metrics_parser.metrics_parser import MetricsParser


def test_parse_valid_quality_metrics(passing_report_path: Path):
    # GIVEN a valid quality metrics file path

    # WHEN parsing the file
    MetricsParser.parse_samples_results(passing_report_path)

    # THEN no error is thrown