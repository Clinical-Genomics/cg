from cg.models.fohm.reports import FohmComplementaryReport, FohmPangolinReport


def test_instantiate_fohm_complementary_report(fohm_complementary_report_raw: dict[str, str]):
    """Tests report dict against a pydantic FohmComplementaryReport."""

    # GIVEN report dicts

    # WHEN instantiating a FOHM report object
    fohm_report = FohmComplementaryReport.model_validate(fohm_complementary_report_raw)

    # THEN assert that it was successfully created
    assert isinstance(fohm_report, FohmComplementaryReport)


def test_instantiate_fohm_pangolin_report(fohm_pangolin_report_raw: dict[str, str]):
    """Tests report dict against a pydantic FohmPangolinReport."""

    # GIVEN report dicts

    # WHEN instantiating a FOHM report object
    fohm_report = FohmPangolinReport.model_validate(fohm_pangolin_report_raw)

    # THEN assert that it was successfully created
    assert isinstance(fohm_report, FohmPangolinReport)
