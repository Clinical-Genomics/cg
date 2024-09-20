import logging
from functools import wraps

from pydantic import ValidationError

from cg.exc import HousekeeperFileMissingError
from cg.services.illumina.sample_sheet.exc import SampleSheetValidationError

LOG = logging.getLogger(__name__)


def handle_missing_or_invalid_sample_sheet_in_hk(func):
    """Log an error and return False when a sample sheet is missing from Housekeeper."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except HousekeeperFileMissingError as error:
            LOG.error(f"Sample sheet not found in Housekeeper: {error}")
            return False

    return wrapper


def handle_sample_sheet_errors(func):
    """Log an error and return False when a SampleSheetValidationError occurs."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SampleSheetValidationError as error:
            LOG.error(f"Sample sheet failed validation: {error}")
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
