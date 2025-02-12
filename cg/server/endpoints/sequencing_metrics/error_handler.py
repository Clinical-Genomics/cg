import logging
from functools import wraps
from http import HTTPStatus

from flask import jsonify

from cg.store.exc import EntryNotFoundError

LOG = logging.getLogger(__name__)


def handle_endpoint_errors(func):

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except EntryNotFoundError as error:
            LOG.error(error)
            return jsonify(error=str(error)), HTTPStatus.NOT_FOUND
        except Exception as error:
            LOG.error(f"Unexpected error in flow cells endpoint: {error}")
            return (
                jsonify(error="An error occurred while processing your request."),
                HTTPStatus.INTERNAL_SERVER_ERROR,
            )

    return wrapper
