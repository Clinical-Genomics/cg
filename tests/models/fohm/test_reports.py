from cg.models.fohm.reports import FohmComplementaryReport


def test_instantiate_fohm_report(fohm_complementary_reports_raw: dict[str, str]):
    """Tests report dict against a pydantic FohmComplementaryReport."""

    # GIVEN report dicts

    # WHEN instantiating a FOHM report object
    fohm_report = FohmComplementaryReport.model_validate(fohm_complementary_reports_raw)

    # THEN assert that it was successfully created
    assert isinstance(fohm_report, FohmComplementaryReport)
