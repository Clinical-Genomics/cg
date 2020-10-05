""" Trailblazer API for cg """ ""

import logging
import json
from google.auth.crypt import RSASigner
from google.auth import jwt
import requests
import datetime as dt

LOG = logging.getLogger(__name__)


class TrailblazerAPI:
    """Interface to Trailblazer for `cg`."""

    __STARTED_STATUSES = ["completed", "failed", "pending", "running"]

    def __init__(self, config: dict):
        self.service_account = config["trailblazer"]["service_account"]
        self.service_account_auth_file = config["trailblazer"]["service_account_auth_file"]
        self.host = config["trailblazer"]["host"]

    @property
    def auth_header(self):
        signer = RSASigner.from_service_account_file(self.service_account_auth_file)
        payload = {"email": self.service_account}
        jwt_token = jwt.encode(signer=signer, payload=payload).decode("ascii")
        auth_header = {"Authorization": f"Bearer {jwt_token}"}
        LOG.info(f"Using header {json.dumps(auth_header)}")
        return auth_header

    def query_trailblazer(self, command: str, request_body: dict) -> str:
        url = self.host + "/query/" + command
        response = requests.post(
            url=url,
            headers=self.auth_header,
            json=request_body,
        )
        return response.text

    def analyses(
        self,
        case_id: str = None,
        query: str = None,
        status: str = None,
        deleted: bool = None,
        temp: bool = False,
        before: dt.datetime = None,
        is_visible: bool = None,
    ):
        request_body = {
            "analyses": {
                "case_id": case_id,
                "status": status,
                "query": query,
                "deleted": deleted,
                "temp": temp,
                "before": before,
                "is_visible": is_visible,
            }
        }
        response_text = self.query_trailblazer(command="analyses", request_body=request_body)
        LOG.info(response_text)

    def get_latest_analysis(self, case_id: str):
        request_body = {
            "case_id": case_id,
        }
        response_text = self.query_trailblazer(
            command="get-latest-analysis", request_body=request_body
        )
        LOG.info(response_text)

    def has_latest_analysis_started(self, case_id: str):
        pass

    def delete_analysis(self, case_id: str, date: dt.datetime):
        pass

    def find_analysis(self, case_id, started_at, status):
        pass

    def mark_analyses_deleted(self, case_id: str) -> None:
        """Mark all analyses for case deleted without removing analysis files"""
        pass

    def add_pending_analysis(self, case_id: str, email: str = None) -> None:
        pass
