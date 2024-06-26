from pathlib import Path

import pytest

from cg.constants import FileExtensions
from cg.meta.upload.fohm.fohm import FOHMUploadAPI
from cg.models.fohm.reports import FohmComplementaryReport, FohmPangolinReport


def test_create_daily_delivery(fohm_upload_api: FOHMUploadAPI, csv_file_path: Path):
    # GIVEN a list of csv files

    # WHEN creating the delivery content
    content: list[dict] = fohm_upload_api.create_daily_deliveries([csv_file_path, csv_file_path])

    # THEN each file is a list of dicts where each dict is a row in a CSV file
    assert isinstance(content[0], dict)

    # THEN two files are added a list of dicts
    assert len(content) == 6


def test_validate_fohm_complementary_reports(
    fohm_upload_api: FOHMUploadAPI, fohm_complementary_report_raw: dict[str, str]
):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[FohmComplementaryReport] = fohm_upload_api.validate_fohm_complementary_reports(
        [fohm_complementary_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmComplementaryReport)


def test_validate_fohm_pangolin_reports(
    fohm_upload_api: FOHMUploadAPI, fohm_pangolin_report_raw: dict[str, str]
):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[FohmPangolinReport] = fohm_upload_api.validate_fohm_pangolin_reports(
        [fohm_pangolin_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmPangolinReport)


def test_get_sars_cov_complementary_reports(
    fohm_complementary_reports: list[FohmComplementaryReport], fohm_upload_api: FOHMUploadAPI
):
    # GIVEN a list of reports

    # WHEN matching values in reports
    content: list[FohmComplementaryReport] = fohm_upload_api.get_sars_cov_complementary_reports(
        fohm_complementary_reports
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmComplementaryReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(content) == 1
    assert content[0].sample_number == "44CS000000"


def test_get_sars_cov_pangolin_reports(
    fohm_pangolin_reports: list[FohmPangolinReport], fohm_upload_api: FOHMUploadAPI
):
    # GIVEN a list of reports

    # WHEN matching values
    content: list[FohmPangolinReport] = fohm_upload_api.get_sars_cov_pangolin_reports(
        fohm_pangolin_reports
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmPangolinReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(content) == 1
    assert content[0].taxon == "44CS000001"


@pytest.fixture
def test_add_sample_internal_id_complementary_report(
    fohm_complementary_reports: list[FohmComplementaryReport], fohm_upload_api: FOHMUploadAPI
):
    """Test adding sample internal id to the reports."""
    # GIVEN a FOHM upload API

    # GIVEN a list of complementary reports

    # WHEN adding sample internal id
    fohm_upload_api.add_sample_internal_id_complementary_report(fohm_complementary_reports)

    # THEN a sample internal id has been added
    assert isinstance(fohm_complementary_reports[0].internal_id, str)


@pytest.fixture
def test_add_sample_internal_id_pangolin_report(
    fohm_pangolin_reports: list[FohmPangolinReport], fohm_upload_api: FOHMUploadAPI
):
    """Test adding sample internal id to the reports."""
    # GIVEN a FOHM upload API

    # GIVEN a list of Pangolin reports

    # WHEN adding sample internal id
    fohm_upload_api.add_sample_internal_id_pangolin_report(fohm_pangolin_reports)

    # THEN a sample internal id has been added
    assert isinstance(fohm_pangolin_reports[0].internal_id, str)


@pytest.fixture
def test_add_region_lab_to_reports(
    fohm_pangolin_reports: list[FohmPangolinReport], fohm_upload_api: FOHMUploadAPI
):
    """Test adding sample internal id to the reports."""
    # GIVEN a FOHM upload API

    # GIVEN a list of Pangolin reports

    # WHEN adding region lab
    fohm_upload_api.add_region_lab_to_reports(fohm_pangolin_reports)

    # THEN a region lab has been added
    assert isinstance(fohm_pangolin_reports[0].region_lab, str)


def test_create_pangolin_reports_csv(
    fohm_pangolin_reports: list[FohmPangolinReport], fohm_upload_api: FOHMUploadAPI
):
    # GIVEN a list of reports

    # GIVEN report folders exist
    fohm_upload_api.create_daily_delivery_folders()

    # GIVEN an outdata path for reports
    pangolin_report_file = Path(
        fohm_upload_api.daily_rawdata_path,
        f"None_{fohm_upload_api.current_datestr}_pangolin_classification_format4{FileExtensions.TXT}",
    )

    # GIVEN that the Pangolin report path does not exist
    assert not pangolin_report_file.exists()

    # WHEN creating reports
    fohm_upload_api.create_pangolin_report_(fohm_pangolin_reports)

    # THEN a file with reports id generated
    assert pangolin_report_file.exists()


def test_create_complementary_report(
    fohm_complementary_reports: list[FohmComplementaryReport], fohm_upload_api: FOHMUploadAPI
):
    # GIVEN a list of reports

    # GIVEN report folders exist
    fohm_upload_api.create_daily_delivery_folders()

    # GIVEN an outdata path for reports
    complementary_report_file = Path(
        fohm_upload_api.daily_report_path,
        f"None_{fohm_upload_api.current_datestr}_komplettering{FileExtensions.CSV}",
    )

    # GIVEN that the Pangolin report path does not exist
    assert not complementary_report_file.exists()

    # WHEN creating reports
    fohm_upload_api.create_and_write_complementary_report(fohm_complementary_reports)

    # THEN a file with reports id generated
    assert complementary_report_file.exists()
