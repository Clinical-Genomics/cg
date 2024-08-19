from cg.meta.upload.gisaid.models import GisaidAccession
from cg.models.gisaid.reports import GisaidComplementaryReport


def test_instantiate_gisaid_accession(gisaid_log_raw: list[dict[str, str]]):
    """Tests report dict against a pydantic GisaidAccession."""

    # GIVEN a raw GISAID log

    # WHEN instantiating a model object
    gisaid_accession = GisaidAccession(log_message=gisaid_log_raw[0].get("msg"))

    # THEN assert that it was successfully created
    assert isinstance(gisaid_accession, GisaidAccession)

    assert isinstance(gisaid_accession.accession_nr, str)


def test_instantiate_gisaid_complementary_report(gisaid_complementary_report_raw: dict[str, str]):
    """Tests report dict against a pydantic GisaidomplementaryReport."""

    # GIVEN report dicts

    # WHEN instantiating a report object
    report = GisaidComplementaryReport.model_validate(gisaid_complementary_report_raw)

    # THEN assert that it was successfully created
    assert isinstance(report, GisaidComplementaryReport)
