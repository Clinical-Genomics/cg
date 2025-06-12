import logging
from functools import wraps


from cg.services.deliver_files.file_fetcher.exc import NoDeliveryFilesError

LOG = logging.getLogger(__name__)


def handle_no_delivery_files_error(func):
    """
    Excepts NoDeliveryFilesError and returns.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NoDeliveryFilesError as error:
            LOG.error(error)
            return

    return wrapper
