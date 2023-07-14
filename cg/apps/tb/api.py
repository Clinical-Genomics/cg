""" Trailblazer API for cg """ ""
import datetime
import datetime as dt
import logging
from typing import Any, Optional

from google.auth import jwt
from google.auth.crypt import RSASigner

from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Pipeline
from cg.constants.constants import APIMethods, FileFormat, WorkflowManager
from cg.constants.priority import SlurmQos
from cg.constants.tb import AnalysisStatus
from cg.exc import TrailblazerAPIHTTPError
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
        url = self.host + "/" + command
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

    def analyses(
        self,
        case_id: str = None,
        query: str = None,
        status: str = None,
        deleted: bool = None,
        temp: bool = False,
        before: dt.datetime = None,
        is_visible: bool = None,
        family: str = None,
        data_analysis: Pipeline = None,
    ) -> list:
        request_body = {
            "case_id": case_id,
            "status": status,
            "query": query,
            "deleted": deleted,
            "temp": temp,
            "before": str(before) if before else None,
            "is_visible": is_visible,
            "family": family,
            "data_analysis": data_analysis.upper() if data_analysis else None,
        }
        response = self.query_trailblazer(command="query-analyses", request_body=request_body)
        if response:
            if isinstance(response, list):
                return [TrailblazerAnalysis.parse_obj(analysis) for analysis in response]
            if isinstance(response, dict):
                return [TrailblazerAnalysis.parse_obj(response)]
        return response

    def get_latest_analysis(self, case_id: str) -> Optional[TrailblazerAnalysis]:
        request_body = {
            "case_id": case_id,
        }
        response = self.query_trailblazer(command="get-latest-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.parse_obj(response)

    def get_latest_analysis_status(self, case_id: str) -> Optional[str]:
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

    def mark_analyses_deleted(self, case_id: str) -> Optional[list]:
        """Mark all analyses for case deleted without removing analysis files"""
        request_body = {
            "case_id": case_id,
        }
        response = self.query_trailblazer(
            command="mark-analyses-deleted", request_body=request_body
        )
        if response:
            if isinstance(response, list):
                return [TrailblazerAnalysis.parse_obj(analysis) for analysis in response]
            if isinstance(response, dict):
                return [TrailblazerAnalysis.parse_obj(response)]

    def add_pending_analysis(
        self,
        case_id: str,
        analysis_type: str,
        config_path: str,
        out_dir: str,
        slurm_quality_of_service: SlurmQos,
        email: str = None,
        data_analysis: Pipeline = None,
        ticket: str = None,
        workflow_manager: str = WorkflowManager.Slurm,
    ) -> TrailblazerAnalysis:
        request_body = {
            "case_id": case_id,
            "email": email,
            "type": analysis_type,
            "config_path": config_path,
            "out_dir": out_dir,
            "priority": slurm_quality_of_service,
            "data_analysis": str(data_analysis).upper(),
            "ticket": ticket,
            "workflow_manager": workflow_manager,
        }
        LOG.debug("Submitting job to Trailblazer: %s", request_body)
        response = self.query_trailblazer(command="add-pending-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.parse_obj(response)

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
