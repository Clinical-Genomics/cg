"""Module that holds the error handlers for the Post Processing service."""

import logging
from cg.exc import CgError

LOG = logging.getLogger(__name__)


def handle_post_processing_errors(to_except: tuple, to_raise):
    """Handle errors for the Post processing services."""

    def error_handling(fn):
        def wrapper(*args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except to_except as error:
                LOG.debug(error)
                raise to_raise(error) from error
            except Exception as error:
                LOG.error(error)
                raise CgError(
                    f"An unexpected error occurred during Post-processing: {error}"
                ) from error

        return wrapper

    return error_handling
