import datetime
import logging
from pathlib import Path

from housekeeper.store.models import File

from cg.apps.housekeeper.hk import HousekeeperAPI

LOG = logging.getLogger(__name__)


class CleanRetrievedSpringFilesAPI:
    """API for cleaning archived Spring files which have been retrieved."""

    def __init__(self, housekeeper_api: HousekeeperAPI, dry_run: bool):
        self.housekeeper_api: HousekeeperAPI = housekeeper_api
        self.dry_run = dry_run

    def _get_files_to_remove(self, days_since_retrieval: int) -> list[File]:
        """Returns all Spring files which were retrieved more than given amount of days ago."""
        return self.housekeeper_api.get_spring_files_retrieved_before(
            date=datetime.datetime.now() - datetime.timedelta(days=days_since_retrieval)
        )

    def _unlink_files(self, files_to_unlink: list[File]) -> None:
        for file in files_to_unlink:
            file_path: str = file.full_path
            if self.dry_run:
                LOG.info(f"Dry run - would have unlinked {file_path}")
            LOG.info(f"Unlinking {file_path}")
            Path(file_path).unlink(missing_ok=True)

    def clean_retrieved_spring_files(self, days_since_retrieval: int):
        """Removes Spring files retrieved more than given amount of days ago from Hasta,
        and resets retrieval data in Housekeeper."""
        files_to_remove: list[File] = self._get_files_to_remove(days_since_retrieval)
        self._unlink_files(files_to_remove)
        if not self.dry_run:
            self.housekeeper_api.reset_retrieved_archive_data(files_to_remove)
        else:
            LOG.info("Would have reset the files' retrieval data")
