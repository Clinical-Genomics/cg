from pathlib import Path

from cg.meta.upload.fohm.fohm import create_daily_deliveries_csv


def test_create_daily_delivery(csv_file_path: Path):
    # GIVEN a list of csv files

    # WHEN creating the delivery content
    content: list[list[dict]] = create_daily_deliveries_csv([csv_file_path, csv_file_path])

    # THEN
    assert isinstance(content[0], dict)
    print(content)
    assert len(content) == 3
