"""Module for the collect qc metrics meta api."""

import logging
from typing import Iterator

from housekeeper.store.models import File, Tag

from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import (
    CreateQCMetricsRequest,
    FilePathAndTag,
)
from cg.clients.janus.exceptions import JanusClientError, JanusServerError
from cg.constants.housekeeper_tags import JanusTags
from cg.exc import HousekeeperFileMissingError
from cg.meta.meta import MetaAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Case, Sample

LOG = logging.getLogger(__name__)


class CollectQCMetricsAPI(MetaAPI):
    """Collect qc metrics API."""

    def __init__(self, config: CGConfig):
        super().__init__(config)
        self.janus_api: JanusAPIClient = config.janus_api
        self.arnold_api: ArnoldAPIClient = config.arnold_api

    def get_qc_metrics_file_paths_for_case(self, case_id: str) -> list[File]:
        """Get the multiqc metrics files for a case."""
        files: list[File] = self.housekeeper_api.get_files(
            bundle=case_id, tags=JanusTags.tags_to_retrieve
        ).all()
        if not files:
            raise HousekeeperFileMissingError(f"No qc metrics files found for {case_id}.")
        return files

    @staticmethod
    def get_tag_to_include(tags: list[Tag]) -> str:
        """Get the multiqc module file tag."""
        for tag in tags:
            if tag.name in JanusTags.multi_qc_file_tags:
                return tag.name

    def get_file_paths_and_tags(self, files: list[File]) -> list[FilePathAndTag]:
        """Get the file path and tag for the multiqc files."""
        file_paths_and_tags: list[FilePathAndTag] = []
        for file_path_and_tags in files:
            file_path: str = file_path_and_tags.full_path
            tag: str = self.get_tag_to_include(file_path_and_tags.tags)
            file_paths_and_tags.append(FilePathAndTag(file_path=file_path, tag=tag))
        return file_paths_and_tags

    def get_prep_category(self, case_id: str) -> str:
        """Get the prep category."""
        samples: list[Sample] = self.status_db.get_samples_by_case_id(case_id)
        return samples[0].prep_category

    def create_qc_metrics_request(self, case_id: str) -> CreateQCMetricsRequest:
        """Create a qc metrics request."""
        files: list[File] = self.get_qc_metrics_file_paths_for_case(case_id)
        file_paths_and_tags: list[FilePathAndTag] = self.get_file_paths_and_tags(files)
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        workflow: str = case.data_analysis
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id)
        prep_category: str = self.get_prep_category(case_id)
        return CreateQCMetricsRequest(
            case_id=case_id,
            sample_ids=sample_ids,
            workflow=workflow,
            prep_category=prep_category,
            files=file_paths_and_tags,
        )

    def get_qc_metrics(self, case_id) -> dict:
        """Get the qc metrics for a case."""
        qc_metrics_request: CreateQCMetricsRequest = self.create_qc_metrics_request(case_id)
        try:
            qc_metrics: dict = self.janus_api.qc_metrics(qc_metrics_request)
            return qc_metrics
        except (JanusClientError, JanusServerError) as error:
            LOG.info(f"Cannot collect qc metrics from Janus: {error}")
