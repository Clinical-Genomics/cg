from pathlib import Path

from cg.meta.upload.fohm.fohm import (
    create_daily_deliveries_csv,
    get_kompletterings_reports,
    get_pangolin_reports,
    remove_duplicate_dicts,
    validate_fohm_reports,
)
from cg.models.fohm.reports import FohmReport


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


def test_validate_fohm_reports(fohm_reports_raw: dict[str, str]):
    # GIVEN a list of dicts

    # WHEN matching values
    content: list[FohmReport] = validate_fohm_reports(reports=[fohm_reports_raw])

    # THEN a list of models is returned
    assert isinstance(content[0], FohmReport)


def test_get_kompletterings_reports(fohm_reports):
    # GIVEN a list of reports

    # WHEN matching values in reports
    content: list[FohmReport] = get_kompletterings_reports(reports=fohm_reports)

    # THEN a list of reports is returned
    assert isinstance(content[0], FohmReport)

    # THEN only dict for complementary reports remains
    assert len(content) == 1
    assert content[0].sample_number == "44CS000000"


def test_get_pangolin_reports():
    # GIVEN a list of dicts
    dicts = [{"taxon": "1CS", "b": 2}, {"c": 1, "taxon": "44CS000001"}]

    # WHEN matching values
    content: list[dict] = get_pangolin_reports(reports=dicts)

    # THEN a list of dicts is returned
    assert isinstance(content[0], dict)

    # THEN only dict for Pangolin reports remains
    assert len(content[0]) == 2
    assert len(content) == 1
