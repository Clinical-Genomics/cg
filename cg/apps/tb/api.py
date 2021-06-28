""" Trailblazer API for cg """ ""
import datetime as dt
import json
import logging
from typing import Any, Optional

import requests
from google.auth import jwt
from google.auth.crypt import RSASigner

from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants import Pipeline
from cg.constants.tb import AnylysisStatus
from cg.exc import TrailblazerAPIHTTPError

LOG = logging.getLogger(__name__)


class TrailblazerAPI:
    """Interface to Trailblazer for `cg`."""

    __STARTED_STATUSES = [
        AnylysisStatus.COMPLETED,
        AnylysisStatus.FAILED,
        AnylysisStatus.PENDING,
        AnylysisStatus.RUNNING,
        AnylysisStatus.ERROR,
    ]
    __ONGOING_STATUSES = [AnylysisStatus.PENDING, AnylysisStatus.RUNNING, AnylysisStatus.ERROR]

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

    def query_trailblazer(self, command: str, request_body: dict) -> Any:
        url = self.host + "/" + command
        LOG.debug(f"REQUEST HEADER {self.auth_header}")
        LOG.debug(f"POST: URL={url}; JSON={request_body}")
        response = requests.post(
            url=url,
            headers=self.auth_header,
            json=request_body,
        )
        LOG.debug(f"RESPONSE STATUS CODE {response.status_code}")
        if not response.ok:
            raise TrailblazerAPIHTTPError(
                f"Request {command} failed with status code {response.status_code}: {response.text}"
            )
        LOG.debug(f"RESPONSE BODY {response.text}")
        return json.loads(response.text)

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

    def find_analysis(
        self, case_id: str, started_at: dt.datetime, status: str
    ) -> Optional[TrailblazerAnalysis]:
        request_body = {"case_id": case_id, "started_at": str(started_at), "status": status}
        response = self.query_trailblazer(command="find-analysis", request_body=request_body)
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
        return self.get_latest_analysis_status(case_id=case_id) == AnylysisStatus.COMPLETED

    def delete_analysis(self, analysis_id: str, force: bool = False) -> None:
        """Raises TrailblazerAPIHTTPError"""
        request_body = {"analysis_id": analysis_id, "force": force}
        self.query_trailblazer(command="delete-analysis", request_body=request_body)

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
        priority: str,
        email: str = None,
        data_analysis: Pipeline = None,
    ) -> TrailblazerAnalysis:
        request_body = {
            "case_id": case_id,
            "email": email,
            "type": analysis_type,
            "config_path": config_path,
            "out_dir": out_dir,
            "priority": priority,
            "data_analysis": str(data_analysis).upper(),
        }
        LOG.debug("Submitting job to Trailblazer: %s", request_body)
        response = self.query_trailblazer(command="add-pending-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.parse_obj(response)
