""" Trailblazer API for cg """ ""
from typing import Any
import logging
import json
from google.auth.crypt import RSASigner
from google.auth import jwt
import requests
import datetime as dt
from cg.exc import TrailblazerAPIHTTPError
from cg.apps.tb.models import TrailblazerAnalysis

LOG = logging.getLogger(__name__)


class TrailblazerAPI:
    """Interface to Trailblazer for `cg`."""

    __STARTED_STATUSES = ["completed", "failed", "pending", "running"]
    __ONGOING_STATUSES = ["pending", "running"]

    def __init__(self, config: dict):
        self.service_account = config["trailblazer"]["service_account"]
        self.service_account_auth_file = config["trailblazer"]["service_account_auth_file"]
        self.host = config["trailblazer"]["host"]

    @property
    def auth_header(self) -> dict:
        signer = RSASigner.from_service_account_file(self.service_account_auth_file)
        payload = {"email": self.service_account}
        jwt_token = jwt.encode(signer=signer, payload=payload).decode("ascii")
        auth_header = {"Authorization": f"Bearer {jwt_token}"}
        return auth_header

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
        LOG.info(response.text, type(json.loads(response.text)))
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
    ) -> list:
        request_body = {
            "analyses": {
                "case_id": case_id,
                "status": status,
                "query": query,
                "deleted": deleted,
                "temp": temp,
                "before": str(before) if before else None,
                "is_visible": is_visible,
                "family": family,
            }
        }
        response = self.query_trailblazer(command="query-analyses", request_body=request_body)
        if response:
            return [TrailblazerAnalysis.parse_obj(analysis) for analysis in response]
        return response

    def get_latest_analysis(self, case_id: str) -> TrailblazerAnalysis:
        request_body = {
            "case_id": case_id,
        }
        response = self.query_trailblazer(command="get-latest-analysis", request_body=request_body)
        return TrailblazerAnalysis.parse_obj(response)

    def find_analysis(
        self, case_id: str, started_at: dt.datetime, status: str
    ) -> TrailblazerAnalysis:
        request_body = {"case_id": case_id, "started_at": str(started_at), "status": status}
        response = self.query_trailblazer(command="find-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.parse_obj(response)

    def get_latest_analysis_status(self, case_id: str) -> str:
        latest_analysis = self.get_latest_analysis(case_id=case_id)
        latest_analysis_status = latest_analysis.status
        return latest_analysis_status

    def has_latest_analysis_started(self, case_id: str) -> bool:
        latest_analysis = self.get_latest_analysis(case_id=case_id)
        latest_analysis_status = latest_analysis.status
        if latest_analysis_status in self.__STARTED_STATUSES:
            return True

    def is_latest_analysis_ongoing(self, case_id: str) -> bool:
        latest_analysis = self.get_latest_analysis(case_id=case_id)
        latest_analysis_status = latest_analysis.status
        if latest_analysis_status in self.__ONGOING_STATUSES:
            return True

    def delete_analysis(self, case_id: str, date: dt.datetime) -> TrailblazerAnalysis:
        """Raises TrailblazerAPIHTTPError"""
        request_body = {"case_id": case_id, "date": str(date)}
        response = self.query_trailblazer(command="delete-analysis", request_body=request_body)
        if response:
            return TrailblazerAnalysis.parse_obj(response)

    def mark_analyses_deleted(self, case_id: str) -> list:
        """Mark all analyses for case deleted without removing analysis files"""
        request_body = {
            "case_id": case_id,
        }
        response = self.query_trailblazer(
            command="mark-analyses-deleted", request_body=request_body
        )
        if response:
            return [TrailblazerAnalysis.parse_obj(analysis) for analysis in response]
        return response

    def add_pending_analysis(self, case_id: str, email: str = None) -> TrailblazerAnalysis:
        request_body = {"case_id": case_id, "email": email}
        response = self.query_trailblazer(command="add-pending-analysis", request_body=request_body)
        return TrailblazerAnalysis.parse_obj(response)
