from typing import Optional, List

from sqlalchemy.orm import Query

from cg.constants.constants import SampleType
from cg.store.models import Sample


def get_sample_by_sample_id(internal_id: str, samples: Query, **kwargs) -> Query:
    """Return sample with sample id."""
    return samples.filter_by(internal_id=internal_id)


def get_samples_with_type(samples: Query, tissue_type: SampleType, **kwargs) -> Query:
    """Return samples with sample type."""
    is_tumour: bool = tissue_type == SampleType.TUMOR
    return samples.filter(Sample.is_tumour == is_tumour)


def get_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Return samples with a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.isnot(None))


def get_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Return samples without a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.is_(None))


def get_sample_by_entry_id(entry_id: int, samples: Query, **kwargs) -> Query:
    """Return sample with entry id."""
    return samples.filter_by(id=entry_id)


def apply_sample_filter(
    functions: List[str],
    samples: Query,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    tissue_type: Optional[SampleType] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "get_sample_by_sample_id": get_sample_by_sample_id,
        "get_sample_by_entry_id": get_sample_by_entry_id,
        "get_samples_with_type": get_samples_with_type,
        "get_samples_with_loqusdb_id": get_samples_with_loqusdb_id,
        "get_samples_without_loqusdb_id": get_samples_without_loqusdb_id,
    }
    for function in functions:
        samples: Query = filter_map[function](
            entry_id=entry_id, internal_id=internal_id, samples=samples, tissue_type=tissue_type
        )
    return samples
