"""Utility functions for the downsampledata module."""
from cg.store import Store
from cg.store.models import Family, Sample


def case_exists_in_statusdb(status_db: Store, case_id: str) -> bool:
    """Check if a case exists in StatusDB."""
    case: Family = status_db.get_case_by_internal_id(case_id)
    if case:
        return True
    return False


def sample_exists_in_statusdb(status_db: Store, sample_id: str) -> bool:
    """Check if a sample exists in StatusDB."""
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)
    if sample:
        return True
    return False
