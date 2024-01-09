import datetime
import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI

LOG = logging.getLogger(__name__)


class CleanRetrievedSpringFilesAPI:
    """API for cleaning archived Spring files which have been retrieved."""

    def __init__(self, housekeeper_api: HousekeeperAPI):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api

    def _get_files_to_remove(self) -> list[File]:
        """Returns all Spring files which were retrieved more than 7 days ago."""
        return self.housekeeper_api.get_spring_files_retrieved_before(
            date=datetime.datetime.now() - datetime.timedelta(days=7)
        )

    def clean_retrieved_spring_files(self, dry_run: bool):
        """Removes Spring files which were retrieved more than 7 days ago."""
        files_to_remove: list[File] = self._get_files_to_remove()
        for file in files_to_remove:
            file_path: str = file.full_path
            if dry_run:
                LOG.info("Dry run - would have unlinked file_path")
            LOG.info(f"Unlinking {file_path}")
            Path(file_path).unlink(missing_ok=True)
