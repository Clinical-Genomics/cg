""" Trailblazer API for cg """ ""

import logging
import json
from trailblazer.store import Store
from google.auth.crypt import RSASigner
from google.auth import jwt
import requests

LOG = logging.getLogger(__name__)


class TrailblazerAPI(Store):
    """Interface to Trailblazer for `cg`."""

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config["trailblazer"]["database"],
            families_dir=config["trailblazer"]["root"],
        )
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

    def get_analysis(self, analysis_id: int):
        url = self.host + f"/analyses/{analysis_id}"
        response = requests.get(url=url, headers=self.auth_header)
        LOG.info(response.text)

    def get_analyses(self):
        url = self.host + "/analyses"
        response = requests.get(url=url, headers=self.auth_header)
        LOG.info(response.text)

    def get_analysis_status(self, case_id: str):
        url = self.host + "/query"
        response = requests.post(
            url=url,
            headers=self.auth_header,
            json={"get_latest_analysis_status": {"case_id": case_id}},
        )
        LOG.info(response.text)
