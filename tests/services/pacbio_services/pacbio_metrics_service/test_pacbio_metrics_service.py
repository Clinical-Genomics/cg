from pathlib import Path
from typing import Any

from cg.services.pacbio.metrics.metrics_parser import MetricsParser
from cg.services.pacbio.metrics.models import HiFiMetrics


def test_parse_attributes_from_json(
    pac_bio_metrics_parser: MetricsParser,
    pac_bio_css_report: Path,
):
    """Test to parse the attributes from a PacBio JSON file."""
    # GIVEN a PacBio JSON file and a PacBio metrics parser initialised from the path

    # WHEN parsing the attributes from the JSON file
    attributes: list[dict[str, Any]] = pac_bio_metrics_parser._parse_report(
        json_file=pac_bio_css_report
    )

    # THEN assert that the attributes are parsed correctly
    assert isinstance(attributes, list)
    assert isinstance(attributes[0], dict)
    assert "id" in attributes[0]
    assert "value" in attributes[0]


def test_parse_attributes_to_model(
    pac_bio_metrics_parser: MetricsParser,
    pac_bio_css_report: Path,
    pac_bio_hifi_metrics: HiFiMetrics,
):
    """Test to parse the attributes to a HiFi model."""
    # GIVEN a PacBio JSON file

    # WHEN parsing the attributes to a model
    parsed_hifi_metrics = pac_bio_metrics_parser.parse_attributes_to_model(
        json_file=pac_bio_css_report,
        model=HiFiMetrics,
    )

    # THEN assert that the attributes are parsed to a model correctly
    assert parsed_hifi_metrics == pac_bio_hifi_metrics

    # THEN assert that the percentage is not taken as a fraction
    assert parsed_hifi_metrics.percent_q30 > 1
