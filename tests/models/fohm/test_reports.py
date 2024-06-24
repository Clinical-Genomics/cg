from cg.models.fohm.reports import FohmReport


def test_instantiate_fohm_report(fohm_reports_raw: dict[str, str]):
    """Tests report dict against a pydantic FohmReport."""

    # GIVEN report dicts

    # WHEN instantiating a FOHM report object
    fohm_report = FohmReport(**fohm_reports_raw)

    # THEN assert that it was successfully created
    assert isinstance(fohm_report, FohmReport)
