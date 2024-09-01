from pathlib import Path

import mock

from cg.io.controller import ReadFile
from cg.meta.upload.gisaid import GisaidAPI
from cg.models.gisaid.reports import GisaidComplementaryReport


def test_get_complementary_report_content(gisaid_api: GisaidAPI, csv_file_path: Path):
    # GIVEN a list of CSV files

    # WHEN creating the report content
    content: list[dict] = gisaid_api.get_complementary_report_content(csv_file_path)

    # THEN each file is a list of dicts where each dict represents a row in a CSV file
    assert isinstance(content[0], dict)

    # THEN the file is added as a list of dicts
    assert len(content) == 3


def test_validate_gisaid_complementary_reports(
    gisaid_api: GisaidAPI, gisaid_complementary_report_raw: dict[str, str]
):
    # GIVEN a dict

    # WHEN validating the dict
    content: list[GisaidComplementaryReport] = gisaid_api.validate_gisaid_complementary_reports(
        [gisaid_complementary_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], GisaidComplementaryReport)


def test_get_sars_cov_complementary_reports(
    gisaid_complementary_reports: list[GisaidComplementaryReport],
    gisaid_api: GisaidAPI,
    sars_cov_sample_number: str,
):
    # GIVEN a list of reports

    # WHEN getting, Sars-cov reports from reports
    content: list[GisaidComplementaryReport] = gisaid_api.get_sars_cov_complementary_reports(
        gisaid_complementary_reports
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], GisaidComplementaryReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(content) == 2
    assert content[0].sample_number == sars_cov_sample_number


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


def test_add_gisaid_accession_to_reports(
    gisaid_complementary_reports: list[GisaidComplementaryReport], gisaid_api: GisaidAPI
):
    """Test adding gisaid accession to the reports."""
    # GIVEN a GISAID API

    # GIVEN a list of reports

    # WHEN adding GISAID accession to reports
    gisaid_api.add_gisaid_accession_to_complementary_reports(
        gisaid_accession={gisaid_complementary_reports[0].sample_number: "a_gisaid_accession"},
        reports=[gisaid_complementary_reports[0]],
    )

    # THEN a GISAID accession has been added
    assert isinstance(gisaid_complementary_reports[0].gisaid_accession, str)


def test_parse_and_get_sars_cov_complementary_reports(
    gisaid_complementary_report_raw: dict[str, str],
    gisaid_api: GisaidAPI,
    sars_cov_sample_number: str,
    gisaid_sars_cov_complementary_report_raw: dict[str, str],
):
    """Test getting Sars-cov complementary reports."""
    # GIVEN a GISAID API

    # GIVEN a report with a Sars-cov entry
    raw_reports: list[dict[str, str]] = [
        gisaid_complementary_report_raw,
        gisaid_sars_cov_complementary_report_raw,
    ]

    # WHEN getting, Sars-cov reports
    sars_cov_reports: list[GisaidComplementaryReport] = (
        gisaid_api.parse_and_get_sars_cov_complementary_reports(
            complementary_report_content_raw=raw_reports
        )
    )

    # THEN a sars-cov reports should be returned
    assert isinstance(sars_cov_reports[0], GisaidComplementaryReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(sars_cov_reports) == 1
    assert sars_cov_reports[0].sample_number == sars_cov_sample_number


def test_are_gisaid_samples_uploaded_when_uploaded(
    gisaid_sars_cov_complementary_report_complete_raw: dict[str, str], gisaid_api: GisaidAPI
):
    """Test are GISAID samples uploaded when the report has GISAID accession."""
    # GIVEN a GISAID API

    # GIVEN an already uploaded report
    sars_cov_complementary_report_complete = GisaidComplementaryReport.model_validate(
        gisaid_sars_cov_complementary_report_complete_raw
    )

    # WHEN verifying if GISAID samples are uploaded
    is_uploaded: bool = gisaid_api.are_gisaid_samples_uploaded(
        [sars_cov_complementary_report_complete]
    )

    # THEN return true
    assert is_uploaded


def test_are_gisaid_samples_uploaded_when_not_uploaded(
    gisaid_complementary_reports: list[GisaidComplementaryReport], gisaid_api: GisaidAPI
):
    """Test are GISAID samples uploaded when areport lacks GISAID accession."""
    # GIVEN a GISAID API

    # GIVEN a list of reports

    # WHEN verifying if GISAID samples are uploaded
    is_uploaded: bool = gisaid_api.are_gisaid_samples_uploaded(gisaid_complementary_reports)

    # THEN return false
    assert not is_uploaded


def test_get_gisaid_accession_numbers(
    gisaid_accession_nr: str,
    gisaid_log_raw: list[dict[str, str]],
    gisaid_api: GisaidAPI,
    sars_cov_sample_number: str,
    csv_file_path: Path,
):
    """Test getting GISAID accession numbers from log"""
    # GIVEN a mock file with a size greater than 0
    with mock.patch.object(GisaidAPI, "get_gisaid_log_path", return_value=csv_file_path):

        # GIVEN a raw GISAID log
        with mock.patch.object(ReadFile, "get_content_from_file", return_value=gisaid_log_raw):

            # WHEN getting accession numbers
            accession_number: dict[str, str] = gisaid_api.get_gisaid_accession_numbers("a_case_id")

            # THEN the accession number should be returned
            assert accession_number.get(sars_cov_sample_number) == gisaid_accession_nr
