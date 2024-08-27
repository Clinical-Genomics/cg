import logging
from functools import wraps
from pathlib import Path
from typing import List, Tuple
from tempfile import TemporaryDirectory

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
    """Decorator to handle and log errors in Freshdesk client methods."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as error:
            error_detail = None
            if error.response is not None:
                try:
                    error_detail = error.response.json()
                except ValueError:
                    error_detail = error.response.text

            LOG.error(
                "Failed request to Freshdesk: %s - Status code: %s, Details: %s",
                error,
                error.response.status_code if error.response else "N/A",
                error_detail,
            )
            raise FreshdeskAPIException(error) from error
        except (MissingSchema, ConnectionError) as error:
            LOG.error("Request to Freshdesk failed: %s", error)
            raise FreshdeskAPIException(error) from error
        except ValidationError as error:
            LOG.error("Invalid response from Freshdesk: %s", error)
            raise FreshdeskModelException(error) from error
        except ValueError as error:
            LOG.error("Operation failed: %s", error)
            raise FreshdeskAPIException(error) from error
        except Exception as error:
            LOG.error("Unexpected error in Freshdesk client: %s", error)
            raise FreshdeskAPIException(error) from error

    return wrapper


def prepare_attachments(attachments: List[Path]) -> List[Tuple[str, Tuple[str, bytes]]]:
    """Prepare the attachments for a request."""
    return [
        ("attachments[]", (attachment.name, open(attachment, "rb"))) for attachment in attachments
    ]


def create_temp_attachment_file(content: dict, file_name: Path) -> TemporaryDirectory:
    """Create a file-based attachment."""
    if content and file_name:
        directory = TemporaryDirectory()
        WriteFile.write_file_from_content(
            content=content,
            file_format=FileFormat.JSON,
            file_path=Path(directory.name, "order.json"),
        )
        return directory
    else:
        LOG.error("Content or file path is None. Cannot create file attachment.")
        raise ValueError("Both content and file path must be provided and cannot be None")
