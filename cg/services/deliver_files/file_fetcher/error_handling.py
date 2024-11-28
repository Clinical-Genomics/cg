import logging
from functools import wraps

from cg.exc import HousekeeperBundleVersionMissingError
from cg.store.models import Case

LOG = logging.getLogger(__name__)


def handle_missing_bundle_errors(func):
    """
    Log an error when a Housekeeper bundle version is missing.

    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        case_id: str = kwargs.get("case_id")
        sample_id: str = kwargs.get("sample_id")
        case: Case = kwargs.get("case")
        try:
            return func(*args, **kwargs)
        except HousekeeperBundleVersionMissingError:
            msg: str = "Missing bundles detected for:"
            if case_id:
                msg += f" case {case_id}"
            if sample_id:
                msg += f" sample {sample_id}"
            if case:
                msg += f" case {case.internal_id}"
            LOG.error(msg)
            return []

    return wrapper
