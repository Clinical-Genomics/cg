import logging
from functools import wraps

from cg.exc import CgError
from cg.services.file_delivery.deliver_files_service.exc import DeliveryTypeNotSupported

LOG = logging.getLogger(__name__)


def handle_delivery_type_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DeliveryTypeNotSupported as error:
            LOG.info("Delivery type not supported or no delivery needed. Skipping delivery.")
            return
        except Exception as error:
            raise CgError(f"{error}") from error

    return wrapper
