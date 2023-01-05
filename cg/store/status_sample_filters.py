from alchy import Query
from cg.store import models


def get_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples with a loqusdb ID."""
    return samples.filter(models.Sample.loqusdb_id.isnot(None))


def get_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples without a loqusdb ID."""
    return samples.filter(models.Sample.loqusdb_id.is_(None))


def apply_sample_filter(function: str, samples: Query) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "samples_uploaded_to_loqusdb": get_samples_with_loqusdb_id,
        "samples_not_uploaded_to_loqusdb": get_samples_without_loqusdb_id,
    }
    return filter_map[function](samples=samples)
