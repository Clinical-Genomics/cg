import logging
from functools import wraps

from pydantic import ValidationError

from cg.exc import HousekeeperFileMissingError
from cg.services.illumina.sample_sheet.exc import SampleSheetValidationError

LOG = logging.getLogger(__name__)


def handle_missing_or_invalid_file(func):
    """Log an error when a Housekeeper file is missing or is not valid."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HousekeeperFileMissingError as error:
            LOG.error(error)
            return False

    return wrapper


def handle_sample_sheet_errors(func):
    """Log an error when a SampleSheetValidationError occurs."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SampleSheetValidationError as error:
            LOG.error(error)
            return False

    return wrapper


def handle_value_and_validation_errors(func):
    """Raise a SampleSheetValidation error when the content can't be parsed."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (ValueError, ValidationError) as error:
            raise SampleSheetValidationError from error

    return wrapper
