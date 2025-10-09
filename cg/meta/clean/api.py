import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import WORKFLOW_PROTECTED_TAGS
from cg.store.models import Analysis
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class CleanAPI:
    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI):
        self.status_db = status_db
        self.housekeeper_api = housekeeper_api

    def get_bundle_files(self, before: datetime, workflow: Workflow) -> Iterator[list[File]]:
        """Get any bundle files for a specific version."""

        completed_analyses_for_workflow: list[Analysis] = (
            self.status_db.get_completed_analyses_for_workflow_started_at_before(
                workflow=workflow, started_at_before=before
            )
        )
        LOG.debug(
            f"number of {workflow} analyses before: {before} : {len(completed_analyses_for_workflow)}"
        )
        for analysis in completed_analyses_for_workflow:
            bundle_name = analysis.case.internal_id
            LOG.info(
                f"Version with id {analysis.housekeeper_version_id} found for "
                f"bundle:{bundle_name}; "
                f"workflow: {workflow}; "
            )
            yield self.housekeeper_api.get_files(
                bundle=bundle_name, version=analysis.housekeeper_version_id
            ).all()

    @staticmethod
    def has_protected_tags(file: File, protected_tags_lists: list[list[str]]) -> bool:
        """Check if a file has any protected tags"""

        LOG.info(f"File {file.full_path} has the tags {file.tags}")
        file_tags: list[str] = HousekeeperAPI.get_tag_names_from_file(file)

        _has_protected_tags: bool = False
        for protected_tags in protected_tags_lists:
            if set(protected_tags).issubset(set(file_tags)):
                LOG.debug(
                    f"File {file.full_path} has the protected tag(s) {protected_tags}, skipping."
                )
                _has_protected_tags = True
                break

        if not _has_protected_tags:
            LOG.info(f"File {file.full_path} has no protected tags.")
        return _has_protected_tags

    def get_unprotected_existing_bundle_files(self, before: datetime) -> Iterator[File]:
        """Returns all existing bundle files from analyses started before 'before' that have no protected tags"""

        workflow: Workflow
        for workflow in Workflow:
            protected_tags_lists = WORKFLOW_PROTECTED_TAGS.get(workflow)
            if not protected_tags_lists:
                LOG.debug(f"No protected tags defined for {workflow}, skipping")
                continue

            hk_files: list[File]
            for hk_files in self.get_bundle_files(before=before, workflow=workflow):
                hk_file: File
                for hk_file in hk_files:
                    if self.has_protected_tags(hk_file, protected_tags_lists=protected_tags_lists):
                        continue

                    file_path: Path = Path(hk_file.full_path)
                    if not file_path.exists():
                        LOG.info(f"File {file_path} not on disk.")
                        continue
                    LOG.info(f"File {file_path} found on disk.")
                    yield hk_file
