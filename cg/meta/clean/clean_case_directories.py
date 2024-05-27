import logging
from datetime import datetime
from os import unlink
from os.path import getmtime
from pathlib import Path

from cg.utils.date import get_date_days_ago

LOG = logging.getLogger(__name__)


def clean_directory(directory_to_clean: Path, days_old: int, dry_run: bool):
    """Cleans the old /analysis/cases directories."""
    date_threshold: datetime = get_date_days_ago(days_old)
    for case_dir in directory_to_clean.iterdir():
        case_modified_time: datetime = datetime.fromtimestamp(getmtime(case_dir))
        if case_modified_time < date_threshold:
            if dry_run:
                LOG.info(f"Would have removed {case_dir.as_posix()}")
            else:
                LOG.info(f"Removing case directory {case_dir.as_posix()}")
                unlink(case_dir)
        else:
            LOG.debug(f"Case {case_dir.as_posix()} is not old enough - skipping.")
    LOG.info("Clean up performed successfully.")
