""" Trailblazer API for cg."""

import datetime
import logging
from typing import Any

from google.auth import jwt
from google.auth.crypt import RSASigner

from cg.apps.tb.dto.create_job_request import CreateJobRequest
from cg.apps.tb.dto.summary_response import AnalysisSummary, SummariesResponse
from cg.apps.tb.models import AnalysesResponse, TrailblazerAnalysis
from cg.constants import Workflow
from cg.constants.constants import APIMethods, FileFormat, JobType, WorkflowManager
from cg.constants.priority import SlurmQos
from cg.constants.tb import AnalysisStatus
from cg.exc import (
    AnalysisNotCompletedError,
    TrailblazerAnalysisNotFound,
    TrailblazerAPIHTTPError,
)
from cg.io.controller import APIRequest, ReadStream

LOG = logging.getLogger(__name__)


class TrailblazerAPI:
    """Interface to Trailblazer for `cg`."""

    __STARTED_STATUSES = [
        AnalysisStatus.COMPLETED,
        AnalysisStatus.FAILED,
        AnalysisStatus.PENDING,
        AnalysisStatus.RUNNING,
        AnalysisStatus.ERROR,
        AnalysisStatus.QC,
    ]
    __ONGOING_STATUSES = [
        AnalysisStatus.PENDING,
        AnalysisStatus.RUNNING,
        AnalysisStatus.ERROR,
        AnalysisStatus.QC,
    ]

    def __init__(self, config: dict):
        self.service_account = config["trailblazer"]["service_account"]
        self.service_account_auth_file = config["trailblazer"]["service_account_auth_file"]
        self.host = config["trailblazer"]["host"]

    @property
    def auth_header(self) -> dict:
        signer = RSASigner.from_service_account_file(self.service_account_auth_file)
        payload = {"email": self.service_account}
        jwt_token = jwt.encode(signer=signer, payload=payload).decode("ascii")
        return {"Authorization": f"Bearer {jwt_token}"}

    def query_trailblazer(
        self, command: str, request_body: dict, method: str = APIMethods.POST
    ) -> Any:
        url = f"{self.host}/{command}"
        LOG.debug(f"REQUEST HEADER {self.auth_header}")
        LOG.debug(f"{method}: URL={url}; JSON={request_body}")

        response = APIRequest.api_request_from_content(
            api_method=method, url=url, headers=self.auth_header, json=request_body
        )

        LOG.debug(f"RESPONSE STATUS CODE {response.status_code}")
        if not response.ok:
            raise TrailblazerAPIHTTPError(
                f"Request {command} failed with status code {response.status_code}: {response.text}"
            )
        LOG.debug(f"RESPONSE BODY {response.text}")
        return ReadStream.get_content_from_stream(file_format=FileFormat.JSON, stream=response.text)

    def get_latest_completed_analysis(self, case_id: str) -> TrailblazerAnalysis | None:
        endpoint = f"analyses?case_id={case_id}&status[]={AnalysisStatus.COMPLETED}&limit=1"
        response = self.query_trailblazer(command=endpoint, request_body={}, method=APIMethods.GET)
        validated_response = AnalysesResponse.model_validate(response)
        if validated_response.analyses:
            return validated_response.analyses[0]
        raise TrailblazerAnalysisNotFound(f"No completed analysis found for case {case_id}")

    def get_latest_analysis(self, case_id: str) -> TrailblazerAnalysis | None:
        request_body = {
            "case_id": case_id,
        }
        response = self.query_trailblazer(command="get-latest-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.model_validate(response)

    def get_latest_analysis_status(self, case_id: str) -> str | None:
        latest_analysis = self.get_latest_analysis(case_id=case_id)
        if latest_analysis:
            return latest_analysis.status

    def has_latest_analysis_started(self, case_id: str) -> bool:
        return self.get_latest_analysis_status(case_id=case_id) in self.__STARTED_STATUSES

    def is_latest_analysis_ongoing(self, case_id: str) -> bool:
        return self.get_latest_analysis_status(case_id=case_id) in self.__ONGOING_STATUSES

    def is_latest_analysis_completed(self, case_id: str) -> bool:
        return self.get_latest_analysis_status(case_id=case_id) == AnalysisStatus.COMPLETED

    def is_latest_analysis_qc(self, case_id: str) -> bool:
        return self.get_latest_analysis_status(case_id=case_id) == AnalysisStatus.QC

    def add_pending_analysis(
        self,
        case_id: str,
        analysis_type: str,
        config_path: str,
        out_dir: str,
        slurm_quality_of_service: SlurmQos,
        email: str = None,
        order_id: int | None = None,
        workflow: Workflow = None,
        ticket: str = None,
        workflow_manager: str = WorkflowManager.Slurm,
        tower_workflow_id: str | None = None,
        is_hidden: bool = False,
    ) -> TrailblazerAnalysis:
        request_body = {
            "case_id": case_id,
            "email": email,
            "type": analysis_type,
            "config_path": config_path,
            "order_id": order_id,
            "out_dir": out_dir,
            "priority": slurm_quality_of_service,
            "workflow": workflow.upper(),
            "ticket": ticket,
            "workflow_manager": workflow_manager,
            "tower_workflow_id": tower_workflow_id,
            "is_hidden": is_hidden,
        }
        LOG.debug(f"Submitting job to Trailblazer: {request_body}")
        if response := self.query_trailblazer(
            command="add-pending-analysis", request_body=request_body
        ):
            return TrailblazerAnalysis.model_validate(response)

    def set_analysis_uploaded(self, case_id: str, uploaded_at: datetime) -> None:
        """Set a uploaded at date for a trailblazer analysis."""
        request_body = {"case_id": case_id, "uploaded_at": str(uploaded_at)}

        LOG.debug(f"Setting analysis uploaded at for {request_body}")
        LOG.info(f"{case_id} - uploaded at set to {uploaded_at}")
        self.query_trailblazer(
            command="set-analysis-uploaded", request_body=request_body, method=APIMethods.PUT
        )

    def set_analysis_status(self, case_id: str, status: str) -> datetime:
        """Set an analysis to a given status."""
        request_body = {"case_id": case_id, "status": status}

        LOG.debug(f"Request body: {request_body}")
        LOG.info(f"Setting analysis status to {status} for case {case_id}")
        self.query_trailblazer(
            command="set-analysis-status", request_body=request_body, method=APIMethods.PUT
        )

    def add_comment(self, case_id: str, comment: str):
        """Adding a comment to a trailblazer analysis."""
        request_body = {"case_id": case_id, "comment": comment}

        LOG.debug(f"Request body: {request_body}")
        LOG.info(f"Adding comment: {comment} to case {case_id}")
        self.query_trailblazer(
            command="add-comment", request_body=request_body, method=APIMethods.PUT
        )

    def add_upload_job_to_analysis(self, analysis_id: int, slurm_id: int) -> None:
        create_request = CreateJobRequest(slurm_id=slurm_id, job_type=JobType.UPLOAD)
        request_body: dict = create_request.model_dump()
        self.query_trailblazer(
            command=f"/analysis/{analysis_id}/jobs",
            request_body=request_body,
            method=APIMethods.POST,
        )

    def get_summaries(self, order_ids: list[int]) -> list[AnalysisSummary]:
        orders_param = "orderIds=" + ",".join(map(str, order_ids))
        endpoint = f"summary?{orders_param}"
        response = self.query_trailblazer(command=endpoint, request_body={}, method=APIMethods.GET)
        response_data = SummariesResponse.model_validate(response)
        return response_data.summaries

    def get_analyses_to_deliver(self, order_id: int) -> list[TrailblazerAnalysis]:
        """Return the analyses in the order ready to be delivered."""
        endpoint = (
            f"analyses?orderId={order_id}&status[]={AnalysisStatus.COMPLETED}&delivered=false"
        )
        raw_response = self.query_trailblazer(
            command=endpoint, request_body={}, method=APIMethods.GET
        )
        validated_response = AnalysesResponse.model_validate(raw_response)
        return validated_response.analyses

    def verify_latest_analysis_is_completed(self, case_id: str, force: bool = False) -> None:
        """Raises an AnalysisNotCompletedError if the latest analysis for the case has not completed."""
        if not self.is_latest_analysis_completed(case_id) and not force:
            raise AnalysisNotCompletedError(f"The latest analysis for {case_id} has not completed.")
