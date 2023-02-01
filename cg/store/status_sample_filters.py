from typing import Optional
from alchy import Query
from cg.store.models import Sample


def get_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples with a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.isnot(None))


def get_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples without a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.is_(None))


def get_sample_by_entry_id(samples: Query, entry_id: int, **kwargs) -> Query:
    return samples.filter_by(id=entry_id)


def sample(samples: Query, internal_id: str, **kwargs) -> Query:
    return samples.filter_by(internal_id=internal_id)


def apply_sample_filter(
    function: str, samples: Query, internal_id: Optional[str] = None, entry_id: Optional[int] = None
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "samples_uploaded_to_loqusdb": get_samples_with_loqusdb_id,
        "samples_not_uploaded_to_loqusdb": get_samples_without_loqusdb_id,
        "sample": sample,
        "get_sample_by_entry_id": get_sample_by_entry_id,
    }
    return filter_map[function](samples=samples, internal_id=internal_id, entry_id=entry_id)
