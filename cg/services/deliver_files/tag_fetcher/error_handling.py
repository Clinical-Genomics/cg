from functools import wraps

from cg.exc import CgError
from cg.services.deliver_files.tag_fetcher.exc import (
    FetchDeliveryFileTagsError,
)


def handle_tag_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            raise FetchDeliveryFileTagsError from error
        except Exception as error:
            raise CgError(f"{error}") from error

    return wrapper
