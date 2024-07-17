import math
from pathlib import Path
from typing import Type

import pytest
from _pytest.fixtures import FixtureRequest

from cg.constants.pacbio import CCSAttributeIDs, ControlAttributeIDs
from cg.services.pacbio.metrics.metrics_parser import MetricsParser
from cg.services.pacbio.metrics.models import (
    BaseMetrics,
    ControlMetrics,
    HiFiMetrics,
    PolymeraseMetrics,
    ProductivityMetrics,
    SmrtlinkDatasetsMetrics,
)


def test_metrics_parser_initialisation(pac_bio_smrt_cell_dir: Path):
    """Test the initialisation of the metrics parser."""
    # GIVEN a PacBio SMRT cell path

    # WHEN initialising the metrics parser
    parser = MetricsParser(smrt_cell_path=pac_bio_smrt_cell_dir)

    # THEN the parser is initialised with the expected attributes
    assert isinstance(parser.hifi_metrics, HiFiMetrics)
    assert isinstance(parser.control_metrics, ControlMetrics)
    assert isinstance(parser.productivity_metrics, ProductivityMetrics)
    assert isinstance(parser.polymerase_metrics, PolymeraseMetrics)
    assert isinstance(parser.smrtlink_datasets_metrics, SmrtlinkDatasetsMetrics)


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
        ("pac_bio_raw_data_report", PolymeraseMetrics, "pac_bio_polymerase_metrics", []),
        ("pac_bio_loading_report", ProductivityMetrics, "pac_bio_productivity_metrics", []),
    ],
    ids=["Control", "Hi-Fi", "Polymerase", "Productivity"],
)
def test_parse_report_to_model(
    pac_bio_metrics_parser: MetricsParser,
    report_file_path: str,
    model: Type[BaseMetrics],
    metrics_fixture: str,
    percent_fields: list[str],
    request: FixtureRequest,
):
    """Test to parse the attributes to a metrics model."""
    # GIVEN a metrics parser

    # GIVEN a pac-bio report file
    report_file: Path = request.getfixturevalue(report_file_path)

    # GIVEN a metrics object with the expected parsed metrics
    expected_metrics: BaseMetrics = request.getfixturevalue(metrics_fixture)

    # WHEN parsing the attributes to a given metrics model
    parsed_metrics: BaseMetrics = pac_bio_metrics_parser.parse_report_to_model(
        report_file=report_file, data_model=model
    )

    # THEN the model attributes are the expected ones
    assert parsed_metrics == expected_metrics

    # THEN the percentage fields of the model are not taken as a fraction
    metrics_dict: dict = parsed_metrics.dict(by_alias=True)
    for percent_field in percent_fields:
        assert metrics_dict.get(percent_field) > 1


def test_parse_smrtlink_datasets_file(
    pac_bio_metrics_parser: MetricsParser,
    pac_bio_smrtlink_databases_metrics: SmrtlinkDatasetsMetrics,
):
    """Test to parse the SMRTlink datasets file."""
    # GIVEN a metrics parser

    # WHEN parsing the SMRTlink datasets file
    smrtlink_datasets_metrics: SmrtlinkDatasetsMetrics = (
        pac_bio_metrics_parser.parse_smrtlink_datasets_file()
    )

    # THEN the parsed metrics are the expected ones
    assert smrtlink_datasets_metrics == pac_bio_smrtlink_databases_metrics


def test_productivity_metrics_percentage_attributes(
    pac_bio_productivity_metrics: ProductivityMetrics,
):
    """Test the percentage attributes of the productivity metrics."""
    # GIVEN a productivity metrics object

    # WHEN accessing the percentage attributes
    percentage_p_0: float = pac_bio_productivity_metrics.percentage_p_0
    percentage_p_1: float = pac_bio_productivity_metrics.percentage_p_1
    percentage_p_2: float = pac_bio_productivity_metrics.percentage_p_2

    # THEN the percentage attributes are calculated correctly
    assert math.isclose(percentage_p_0, 40, abs_tol=1e-9)
    assert math.isclose(percentage_p_1, 60, abs_tol=1e-9)
    assert math.isclose(percentage_p_2, 0, abs_tol=1e-9)
