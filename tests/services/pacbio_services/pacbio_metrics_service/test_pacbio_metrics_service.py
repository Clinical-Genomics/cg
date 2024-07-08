from pathlib import Path
from typing import Any, Callable

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.pacbio import CCSAttributeIDs, ControlAttributeIDs
from cg.services.pacbio.metrics.metrics_parser import MetricsParser
from cg.services.pacbio.metrics.models import ControlMetrics, HiFiMetrics


def test_metrics_parser_initialisation(pac_bio_smrt_cell_dir: Path):
    """Test the initialisation of the metrics parser."""
    # GIVEN a PacBio SMRT cell path

    # WHEN initialising the metrics parser
    parser = MetricsParser(smrt_cell_path=pac_bio_smrt_cell_dir)

    # THEN assert that the parser is initialised with the expected attributes
    assert isinstance(parser.hifi_metrics, HiFiMetrics)
    assert isinstance(parser.control_metrics, ControlMetrics)


@pytest.mark.parametrize(
    "report_file_path",
    ["pac_bio_control_report", "pac_bio_css_report"],
)
def test_parse_attributes_from_json(
    pac_bio_metrics_parser: MetricsParser,
    report_file_path: str,
    request: FixtureRequest,
):
    """Test the parsing of attributes from any PacBio report file."""
    # GIVEN a PacBio report file and a PacBio metrics parser initialised from the SMRTcell path
    report_file: Path = request.getfixturevalue(report_file_path)

    # WHEN parsing the report file
    attributes: list[dict[str, Any]] = pac_bio_metrics_parser._parse_report(report_file=report_file)

    # THEN assert that the report attributes are parsed correctly
    assert isinstance(attributes, list)
    assert isinstance(attributes[0], dict)
    assert "id" in attributes[0]
    assert "value" in attributes[0]


@pytest.mark.parametrize(
    "report_file_path, model, metrics_fixture, percent_fields",
    [
        (
            "pac_bio_control_report",
            ControlMetrics,
            "pac_bio_control_metrics",
            [
                ControlAttributeIDs.PERCENT_MEAN_READ_CONCORDANCE,
                ControlAttributeIDs.PERCENT_MODE_READ_CONCORDANCE,
            ],
        ),
        ("pac_bio_css_report", HiFiMetrics, "pac_bio_hifi_metrics", [CCSAttributeIDs.PERCENT_Q30]),
    ],
)
def test_parse_attributes_to_model(
    pac_bio_metrics_parser: MetricsParser,
    report_file_path: str,
    model: Callable,
    metrics_fixture: str,
    percent_fields: list[str],
    request: FixtureRequest,
):
    """Test to parse the attributes to a metrics model."""
    # GIVEN a metrics parser

    # GIVEN a pac-bio report file
    report_file: Path = request.getfixturevalue(report_file_path)

    # GIVEN a metrics object with the expected parsed metrics
    expected_metrics: ControlMetrics | HiFiMetrics = request.getfixturevalue(metrics_fixture)

    # WHEN parsing the attributes to a given metrics model
    parsed_metrics: ControlMetrics | HiFiMetrics = pac_bio_metrics_parser.parse_attributes_to_model(
        report_file=report_file,
        data_model=model,
    )

    # THEN assert that the model attributes are the expected ones
    assert parsed_metrics == expected_metrics

    # THEN assert that the percentage fields of the model are not taken as a fraction
    metrics_dict: dict = parsed_metrics.dict(by_alias=True)
    for percent_field in percent_fields:
        assert metrics_dict.get(percent_field) > 1
