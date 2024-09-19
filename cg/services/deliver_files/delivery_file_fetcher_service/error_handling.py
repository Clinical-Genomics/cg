import logging
from functools import wraps

from pydantic_core import ValidationError

from cg.exc import HousekeeperBundleVersionMissingError
from cg.services.deliver_files.delivery_file_fetcher_service.exc import NoDeliveryFilesError

LOG = logging.getLogger(__name__)


def handle_missing_bundle_errors(func):
    """
    Log an error when a Housekeeper bundle version is missing.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HousekeeperBundleVersionMissingError as error:
            LOG.error(error)
            return None

    return wrapper


def handle_delivery_file_validation_error(func):
    """
    Log an error when a delivery file is invalid.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError:
            raise NoDeliveryFilesError("No files to deliver found.")

    return wrapper
