from functools import wraps

from cg.services.file_delivery.fetch_delivery_files_tags.exc import FetchDeliveryFileTagsError


def handle_tag_fetch_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as error:
            raise FetchDeliveryFileTagsError(f"{error}") from error
        return wrapper

    return decorator
