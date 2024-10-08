import logging
from functools import wraps

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
            return []

    return wrapper
