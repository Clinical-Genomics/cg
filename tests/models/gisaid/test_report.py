from cg.models.gisaid.reports import GisaidComplementaryReport


def test_instantiate_gisaid_complementary_report(gisaid_complementary_report_raw: dict[str, str]):
    """Tests report dict against a pydantic GisaidomplementaryReport."""

    # GIVEN report dicts

    # WHEN instantiating a report object
    report = GisaidComplementaryReport.model_validate(gisaid_complementary_report_raw)

    # THEN assert that it was successfully created
    assert isinstance(report, GisaidComplementaryReport)
