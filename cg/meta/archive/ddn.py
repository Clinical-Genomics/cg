from pathlib import Path
from typing import Dict
from urllib.parse import urljoin

from cg.constants.constants import APIMethods, FileFormat
from cg.io.controller import APIRequest, ReadStream


class DDNApi:
    def __init__(self, config: Path):
        self.config = config
        self.url: str = "some/url"
        self.archive_repo = "archive_name"
        self.source_repo = "probably the HPC?"

    @property
    def auth_header(self) -> dict:
        response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="auth/token"),
            headers={"Content-Type": "application/json", "accept": "application/json"},
            json={
                "dbName": self.db_name,
                "name": self.user,
                "password": self.password,
                "superUser": False,
            },
        )
        auth_token: str = ReadStream.get_content_from_stream(
            file_format=FileFormat.JSON, stream=response.content
        )
        return {"Authorization": f"Bearer {auth_token}"}

    # Todo add json construction logic here
    def archive_folder(self, destination: Path, source: Path):
        payload: dict = {
            "pathInfo": [self._construct_path_dict(destination=destination, source=source)],
            "osType": "linux",
            "createDirectory": "true",
            "metadataList": [{}],
        }
        response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/archive"),
            headers=self.auth_header,
            json=payload,
        )

    def retrieve_folder(self, destination: Path, source: Path):
        payload: dict = {
            "pathInfo": [self._construct_path_dict(destination=destination, source=source)],
            "osType": "linux",
            "createDirectory": "true",
        }
        response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/retrieve"),
            headers=self.auth_header,
            json=payload,
        )

    def _construct_path_dict(self, source, destination) -> Dict[str, str]:
        return {
            "source": "archive@OneOne:/Test./ada_event",
            "destination": "nfs@Nas_1:/Miria/Binary/Adm",
        }
