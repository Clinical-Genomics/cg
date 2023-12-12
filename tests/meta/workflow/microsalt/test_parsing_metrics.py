from pathlib import Path

from cg.meta.workflow.microsalt.utils import parse_quality_metrics


def test_parse_valid_quality_metrics(valid_microsalt_metrics_file: Path):
    # GIVEN a valid quality metrics file path

    # WHEN parsing the file
    parse_quality_metrics(valid_microsalt_metrics_file)

    # THEN no error is thrown
