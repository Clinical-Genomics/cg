import logging
from functools import wraps

from cg.exc import CgError
from cg.services.deliver_files.deliver_files_service.exc import DeliveryTypeNotSupported

LOG = logging.getLogger(__name__)


def handle_delivery_type_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except DeliveryTypeNotSupported:
            LOG.info("Delivery type not supported or no delivery needed. Skipping delivery.")
            return

    return wrapper
