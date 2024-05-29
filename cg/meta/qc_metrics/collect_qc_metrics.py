"""Module for the collect qc metrics meta api."""

import logging
from typing import Iterator

from housekeeper.store.models import File, Tag

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.arnold.dto.create_case_request import CreateCaseRequest
from cg.clients.janus.api import JanusAPIClient
from cg.clients.janus.dto.create_qc_metrics_request import (
    CreateQCMetricsRequest,
    FilePathAndTag,
    WorkflowInfo,
)
from cg.constants.housekeeper_tags import JanusTags
from cg.exc import HousekeeperFileMissingError
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class CollectQCMetricsAPI:
    """Collect qc metrics API."""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        status_db: Store,
        janus_api: JanusAPIClient,
        arnold_api: ArnoldAPIClient,
    ):
        self.hk_api: HousekeeperAPI = hk_api
        self.status_db: Store = status_db
        self.janus_api: JanusAPIClient = janus_api
        self.arnold_api: ArnoldAPIClient = arnold_api

    def get_qc_metrics_file_paths_for_case(self, case_id: str) -> list[File]:
        """Get the multiqc metrics files for a case."""
        files: list[File] = self.hk_api.get_files(
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
        for hk_file in files:
            file_path: str = hk_file.full_path
            tag: str = self.get_tag_to_include(hk_file.tags)
            file_paths_and_tags.append(FilePathAndTag(file_path=file_path, tag=tag))
        return file_paths_and_tags

    @staticmethod
    def get_workflow_info(case: Case) -> WorkflowInfo:
        workflow: str = case.data_analysis
        workflow_version: str = case.analyses[0].workflow_version
        return WorkflowInfo(workflow=workflow, version=workflow_version)

    def create_qc_metrics_request(self, case_id: str) -> CreateQCMetricsRequest:
        """Create a qc metrics request."""
        files: list[File] = self.get_qc_metrics_file_paths_for_case(case_id)
        file_paths_and_tags: list[FilePathAndTag] = self.get_file_paths_and_tags(files)
        case: Case = self.status_db.get_case_by_internal_id(case_id)
        workflow_info: WorkflowInfo = self.get_workflow_info(case)
        sample_ids: Iterator[str] = self.status_db.get_sample_ids_by_case_id(case_id)

        return CreateQCMetricsRequest(
            case_id=case_id,
            sample_ids=sample_ids,
            workflow_info=workflow_info,
            files=file_paths_and_tags,
        )

    def get_case_qc_metrics(self, case_id: str) -> dict:
        """Get the qc metrics for a case."""
        qc_metrics_request: CreateQCMetricsRequest = self.create_qc_metrics_request(case_id)
        qc_metrics: dict = self.janus_api.qc_metrics(qc_metrics_request)
        return qc_metrics

    def get_create_case_request(self, case_id: str) -> CreateCaseRequest:
        case_qc_metrics: dict = self.get_case_qc_metrics(case_id)
        if not case_qc_metrics:
            raise ValueError(f"Could not retrieve qc metrics from Janus for case {case_id}")
        return CreateCaseRequest(**case_qc_metrics)

    def create_case(self, case_id: str, dry_run: bool = False):
        case_request: CreateCaseRequest = self.get_create_case_request(case_id)
        if dry_run:
            LOG.info(f"Would have sent create case request to Arnold with: {case_request}")
            return
        self.arnold_api.create_case(case_request)
