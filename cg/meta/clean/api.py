import logging
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

from housekeeper.store.models import File, Version

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import Pipeline
from cg.constants.housekeeper_tags import WORKFLOW_PROTECTED_TAGS
from cg.store import Store
from cg.store.models import Analysis

LOG = logging.getLogger(__name__)


class CleanAPI:
    def __init__(self, status_db: Store, housekeeper_api: HousekeeperAPI):
        self.status_db = status_db
        self.housekeeper_api = housekeeper_api

    def get_bundle_files(self, before: datetime, pipeline: Pipeline) -> Iterator[list[File]]:
        """Get any bundle files for a specific version"""

        analysis: Analysis
        LOG.debug(
            f"number of {pipeline} analyses before: {before} : {len(self.status_db.get_analyses_for_pipeline_started_at_before(pipeline=pipeline, started_at_before=before))}"
        )

        for analysis in self.status_db.get_analyses_for_pipeline_started_at_before(
            pipeline=pipeline, started_at_before=before
        ):
            bundle_name = analysis.family.internal_id

            hk_bundle_version: Optional[Version] = self.housekeeper_api.version(
                bundle=bundle_name, date=analysis.started_at
            )
            if not hk_bundle_version:
                LOG.warning(
                    f"Version not found for "
                    f"bundle:{bundle_name}; "
                    f"pipeline: {pipeline}; "
                    f"date {analysis.started_at}"
                )
                continue

            LOG.info(
                f"Version found for "
                f"bundle:{bundle_name}; "
                f"pipeline: {pipeline}; "
                f"date {analysis.started_at}"
            )
            yield self.housekeeper_api.get_files(
                bundle=bundle_name, version=hk_bundle_version.id
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
                    "File %s has the protected tag(s) %s, skipping.",
                    file.full_path,
                    protected_tags,
                )
                _has_protected_tags = True
                break

        if not _has_protected_tags:
            LOG.info("File %s has no protected tags.", file.full_path)
        return _has_protected_tags

    def get_unprotected_existing_bundle_files(self, before: datetime) -> Iterator[File]:
        """Returns all existing bundle files from analyses started before 'before' that have no protected tags"""

        pipeline: Pipeline
        for pipeline in Pipeline:
            protected_tags_lists = WORKFLOW_PROTECTED_TAGS.get(pipeline)
            if not protected_tags_lists:
                LOG.debug("No protected tags defined for %s, skipping", pipeline)
                continue

            hk_files: list[File]
            for hk_files in self.get_bundle_files(
                before=before,
                pipeline=pipeline,
            ):
                hk_file: File
                for hk_file in hk_files:
                    if self.has_protected_tags(hk_file, protected_tags_lists=protected_tags_lists):
                        continue

                    file_path: Path = Path(hk_file.full_path)
                    if not file_path.exists():
                        LOG.info("File %s not on disk.", file_path)
                        continue
                    LOG.info("File %s found on disk.", file_path)
                    yield hk_file
