from pathlib import Path

from cg.meta.workflow.microsalt.metrics_parser import MetricsParser


def test_parse_valid_quality_metrics(microsalt_metrics_file: Path):
    # GIVEN a valid quality metrics file path

    # WHEN parsing the file
    MetricsParser.parse(microsalt_metrics_file)

    # THEN no error is thrown
