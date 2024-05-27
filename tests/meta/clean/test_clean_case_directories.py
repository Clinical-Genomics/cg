from datetime import datetime, timedelta
from os import utime
from pathlib import Path

import pytest

from cg.meta.clean.clean_case_directories import clean_directories


@pytest.mark.parametrize("days_since_modification, should_be_cleaned", [(1, False), (100, True)])
def test_clean_case_directories(
    tmp_path: Path,
    days_since_modification: int,
    should_be_cleaned: bool,
):
    """Tests cleaning of case directories."""

    # GIVEN a file which was modified days_since_modification ago
    file_path = Path(tmp_path, "test_file")
    file_path.touch()
    modified_date = datetime.now() - timedelta(days=days_since_modification)
    utime(path=file_path, times=(datetime.now().timestamp(), modified_date.timestamp()))

    # WHEN cleaning the tmp_path/cases directory of old files
    clean_directories(directory_to_clean=tmp_path, days_old=60, dry_run=False)

    # THEN the file should be deleted if it was old.
    assert file_path.exists() != should_be_cleaned
