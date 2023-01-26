from typing import Optional

from alchy import Query

from cg.constants.constants import SampleType
from cg.store.models import Family, Sample


def get_samples_with_case_id(samples: Query, case_id: str, **kwargs) -> Query:
    """Get samples associated with a specific case ID."""
    return samples.filter(Family.internal_id == case_id)


def get_samples_with_type(samples: Query, sample_type: SampleType, **kwargs) -> Query:
    """Get samples by type (tumor/normal)."""
    is_tumour: bool = sample_type == SampleType.TUMOR
    return samples.filter(Sample.is_tumour == is_tumour)


def get_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples with a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.isnot(None))


def get_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Fetches samples without a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.is_(None))


def apply_sample_filter(
    function: str,
    samples: Query,
    case_id: Optional[str] = None,
    sample_type: Optional[SampleType] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "samples_with_case_id": get_samples_with_case_id,
        "samples_with_type": get_samples_with_type,
        "samples_uploaded_to_loqusdb": get_samples_with_loqusdb_id,
        "samples_not_uploaded_to_loqusdb": get_samples_without_loqusdb_id,
    }
    return filter_map[function](samples=samples, case_id=case_id, sample_type=sample_type)
