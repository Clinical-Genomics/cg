from pathlib import Path
from urllib.parse import urljoin

from cg.constants.constants import APIMethods, FileFormat
from cg.io.controller import APIRequest, ReadStream


class DDNApi:
    def __int__(self, config: Path):
        self.config = config
        self.url: str = "some/url"

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
    def archive_folder(self, folder: Path):
        response = APIRequest.api_request_from_content(
            api_method=APIMethods.POST,
            url=urljoin(base=self.url, url="files/archive"),
            headers=self.auth_header,
            json={},
        )

    def retrieve_folder(self, folder: Path):
        response = APIRequest.api_request_from_content(
            api_method=APIMethods.GET,
            url=urljoin(base=self.url, url="files/retrieve"),
            headers=self.auth_header,
            json={},
        )
