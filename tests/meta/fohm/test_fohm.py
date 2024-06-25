from pathlib import Path

import pytest

from cg.meta.upload.fohm.fohm import (
    FOHMUploadAPI,
    create_daily_deliveries_csv,
    get_sars_cov_complementary_reports,
    get_sars_cov_pangolin_reports,
    remove_duplicate_dicts,
    validate_fohm_complementary_reports,
    validate_fohm_pangolin_reports,
)
from cg.models.fohm.reports import FohmComplementaryReport, FohmPangolinReport


def test_create_daily_delivery(csv_file_path: Path):
    # GIVEN a list of csv files

    # WHEN creating the delivery content
    content: list[dict] = create_daily_deliveries_csv(file_paths=[csv_file_path, csv_file_path])

    # THEN each file is a list of dicts where each dict is a row in a CSV file
    assert isinstance(content[0][0], dict)

    # THEN two files are added as two lists of dicts
    assert len(content) == 2


def test_remove_duplicate_dicts():
    # GIVEN a list with a list of dicts
    dicts = [[{"a": 1, "b": 2}, {"c": 1, "d": 4}], [{"a": 1, "b": 2}, {"c": 1, "d": 4}]]

    # WHEN removing duplicate dicts
    content: list[dict] = remove_duplicate_dicts(dicts=dicts)

    # THEN a list of dicts is returned
    assert isinstance(content[0], dict)

    # THEN duplicates are removed
    assert len(content) == 2
    assert len(content[0]) == 2
    assert len(content[1]) == 2


def test_remove_duplicate_dicts_when_no_duplicates():
    # GIVEN a list with a list of dicts
    dicts = [[{"a": 1, "b": 2}, {"c": 1, "d": 4}], [{"f": 1, "b": 2}, {"c": 1, "d": 1}]]

    # WHEN removing duplicate dicts
    content: list[dict] = remove_duplicate_dicts(dicts=dicts)

    # THEN a list of dicts is returned
    assert isinstance(content[0], dict)

    # THEN all dicts remain
    assert len(content) == 4
    assert len(content[3]) == 2


def test_validate_fohm_complementary_reports(fohm_complementary_report_raw: dict[str, str]):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[FohmComplementaryReport] = validate_fohm_complementary_reports(
        reports=[fohm_complementary_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmComplementaryReport)


def test_validate_fohm_pangolin_reports(fohm_pangolin_report_raw: dict[str, str]):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[FohmPangolinReport] = validate_fohm_pangolin_reports(
        reports=[fohm_pangolin_report_raw]
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmPangolinReport)


def test_get_sars_cov_complementary_reports(
    fohm_complementary_reports: list[FohmComplementaryReport],
):
    # GIVEN a list of reports

    # WHEN matching values in reports
    content: list[FohmComplementaryReport] = get_sars_cov_complementary_reports(
        reports=fohm_complementary_reports
    )

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmComplementaryReport)

    # THEN only the report for Sars-cov2 reports remains
    assert len(content) == 1
    assert content[0].sample_number == "44CS000000"


def test_get_sars_cov_pangolin_reports(fohm_pangolin_reports: list[FohmPangolinReport]):
    # GIVEN a list of reports

    # WHEN matching values
    content: list[FohmPangolinReport] = get_sars_cov_pangolin_reports(reports=fohm_pangolin_reports)

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
    fohm_upload_api.add_sample_internal_id_complementary_report(reports=fohm_complementary_reports)

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
    fohm_upload_api.add_sample_internal_id_pangolin_report(reports=fohm_pangolin_reports)

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
    fohm_upload_api.add_region_lab_to_reports(reports=fohm_pangolin_reports)

    # THEN a region lab has been added
    assert isinstance(fohm_pangolin_reports[0].region_lab, str)
