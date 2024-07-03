from pathlib import Path

from cg.meta.upload.gisaid import GisaidAPI
from cg.models.gisaid.reports import GisaidComplementaryReport


def test_get_complementary_report_content(gisaid_api: GisaidAPI, csv_file_path: Path):
    # GIVEN a list of csv files

    # WHEN creating the delivery content
    content: list[dict] = gisaid_api.get_complementary_report_content(csv_file_path)

    # THEN each file is a list of dicts where each dict is a row in a CSV file
    assert isinstance(content[0], dict)

    # THEN two files are added as a list of dicts
    assert len(content) == 3


def test_validate_gisaid_complementary_reports(
    gisaid_api: GisaidAPI, gisaid_complementary_report_raw: dict[str, str]
):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[GisaidComplementaryReport] = gisaid_api.validate_gisaid_complementary_reports(
        [gisaid_complementary_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], GisaidComplementaryReport)


def test_get_sars_cov_complementary_reports(
    gisaid_complementary_reports: list[GisaidComplementaryReport], gisaid_api: GisaidAPI
):
    # GIVEN a list of reports

    # WHEN matching values in reports
    content: list[GisaidComplementaryReport] = gisaid_api.get_sars_cov_complementary_reports(
        gisaid_complementary_reports
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], GisaidComplementaryReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(content) == 1
    assert content[0].sample_number == "44CS000000"


def test_get_complementary_report_sample_number(
    gisaid_complementary_reports: list[GisaidComplementaryReport], gisaid_api: GisaidAPI
):
    # GIVEN a list of reports

    # WHEN getting the sample numbers in the reports
    sample_numbers: set[str] = gisaid_api.get_complementary_report_sample_number(
        gisaid_complementary_reports
    )

    # THEN return sample numbers from reports
    for report in gisaid_complementary_reports:
        assert report.sample_number in sample_numbers
