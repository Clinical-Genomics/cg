import logging
from functools import wraps
from pathlib import Path
from typing import List, Tuple

from pydantic import ValidationError
from requests import ConnectionError, HTTPError
from requests.exceptions import MissingSchema
from cg.constants.constants import FileFormat

from cg.clients.freshdesk.exceptions import (
    FreshdeskAPIException,
    FreshdeskModelException,
)
from cg.io.controller import WriteFile

LOG = logging.getLogger(__name__)
TEXT_FILE_ATTACH_PARAMS = "data:text/plain;charset=utf-8,{content}"


def handle_client_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (MissingSchema, HTTPError, ConnectionError) as error:
            LOG.error(f"Request to Freshdesk failed: {error}")
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error(f"Invalid response from Freshdesk: {error}")
            raise FreshdeskModelException(error) from error
        except Exception as error:
            LOG.error(f"Unexpected error in Freshdesk client: {error}")
            raise FreshdeskAPIException(error) from error

    return wrapper


def prepare_attachments(attachments: List[Path]) -> List[Tuple[str, Tuple[str, bytes]]]:
    """Prepare the attachments for a request."""
    return [
        ("attachments[]", (attachment.name, open(attachment, "rb"))) for attachment in attachments
    ]


def create_file_attachment(content: dict, file_path: Path) -> None:
    """Create a file-based attachment."""
    if content and file_path:
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.JSON,
            file_path=file_path,
        )
    else:
        LOG.error("Content or file path is None. Cannot create file attachment.")
