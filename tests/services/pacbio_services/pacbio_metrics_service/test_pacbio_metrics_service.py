from pathlib import Path
from typing import Callable

import pytest
from _pytest.fixtures import FixtureRequest

from cg.services.pacbio.metrics.models import BaseMetrics
from cg.services.pacbio.metrics.utils import (
    parse_control_metrics,
    parse_dataset_metrics,
    parse_hifi_metrics,
    parse_polymerase_metrics,
    parse_productivity_metrics,
)


@pytest.mark.parametrize(
    "parsing_function, expected_metrics_fixture",
    [
        (parse_control_metrics, "pac_bio_control_metrics"),
        (parse_dataset_metrics, "pac_bio_smrtlink_databases_metrics"),
        (parse_hifi_metrics, "pac_bio_hifi_metrics"),
        (parse_productivity_metrics, "pac_bio_productivity_metrics"),
        (parse_polymerase_metrics, "pac_bio_polymerase_metrics"),
    ],
    ids=["Control", "Smrtlink-Dataset", "Hi-Fi", "Productivity", "Polymerase"],
)
def test_parse_dataset_metrics(
    parsing_function: Callable,
    expected_metrics_fixture: str,
    pac_bio_run_statistics_dir: Path,
    request: FixtureRequest,
):
    """Test the parsing of all PacBio metric files."""
    # GIVEN a metrics file to parse in an existing statistics directory

    # WHEN parsing the SMRTlink datasets metrics
    parsed_metrics: BaseMetrics = parsing_function(report_dir=pac_bio_run_statistics_dir)

    # THEN the parsed metrics are the expected ones
    expected_metrics: BaseMetrics = request.getfixturevalue(expected_metrics_fixture)
    assert parsed_metrics == expected_metrics
