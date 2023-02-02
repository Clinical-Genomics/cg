from typing import Optional

from alchy import Query

from cg.constants.constants import SampleType
from cg.store.models import Sample


def sample(samples: Query, internal_id: str, **kwargs) -> Query:
    return samples.filter_by(internal_id=internal_id)


def get_samples_with_type(samples: Query, tissue_type: SampleType, **kwargs) -> Query:
    """Get samples by type (tumor/normal)."""
    is_tumour: bool = tissue_type == SampleType.TUMOR
    return samples.filter(Sample.is_tumour == is_tumour)


def get_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples with a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.isnot(None))


def get_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples without a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.is_(None))


def get_sample_by_entry_id(samples: Query, entry_id: int, **kwargs) -> Query:
    return samples.filter_by(id=entry_id)


def apply_sample_filter(
    function: str,
    samples: Query,
    internal_id: Optional[str] = None,
    entry_id: Optional[int] = None,
    tissue_type: Optional[SampleType] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "sample": sample,
        "get_samples_with_type": get_samples_with_type,
        "samples_uploaded_to_loqusdb": get_samples_with_loqusdb_id,
        "samples_not_uploaded_to_loqusdb": get_samples_without_loqusdb_id,
        "get_sample_by_entry_id": get_sample_by_entry_id,
    }
    return filter_map[function](
        samples=samples, internal_id=internal_id, entry_id=entry_id, tissue_type=tissue_type
    )
