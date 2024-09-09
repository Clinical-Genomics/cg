import logging
from functools import wraps
from pathlib import Path
from tempfile import TemporaryDirectory

from pydantic import ValidationError
from requests import ConnectionError, HTTPError
from requests.exceptions import MissingSchema

from cg.clients.freshdesk.exceptions import (
    FreshdeskAPIException,
    FreshdeskModelException,
)
from cg.constants.constants import FileFormat
from cg.io.controller import WriteFile

LOG = logging.getLogger(__name__)


def extract_error_detail(error):
    """Extract detailed error information from HTTPError."""
    if error.response is not None:
        try:
            return error.response.json()
        except ValueError:
            return error.response.text
    return None


def log_and_raise(exception_class, message, error):
    """Log the error and raise the appropriate exception."""
    LOG.error(message)
    raise exception_class(error) from error


def handle_client_errors(func):
    """Decorator to handle and log errors in Freshdesk client methods."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HTTPError as error:
            error_detail = extract_error_detail(error)
            log_and_raise(
                FreshdeskAPIException,
                f"Failed request to Freshdesk: {error} - Status code: "
                f"{error.response.status_code if error.response else 'N/A'}, Details: {error_detail}",
                error,
            )
        except (MissingSchema, ConnectionError) as error:
            log_and_raise(FreshdeskAPIException, f"Request to Freshdesk failed: {error}", error)
        except ValidationError as error:
            log_and_raise(
                FreshdeskModelException, f"Invalid response from Freshdesk: {error}", error
            )
        except ValueError as error:
            log_and_raise(FreshdeskAPIException, f"Operation failed: {error}", error)
        except Exception as error:
            log_and_raise(
                FreshdeskAPIException, f"Unexpected error in Freshdesk client: {error}", error
            )

    return wrapper


def prepare_attachments(attachments: list[Path]) -> list[tuple[str, tuple[str, bytes]]]:
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
