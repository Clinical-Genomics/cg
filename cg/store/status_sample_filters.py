from typing import Optional

from alchy import Query

from cg.constants.constants import SampleType
from cg.store.models import Sample, Family


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


def get_samples_by_analysis(samples: Query, data_analysis: str) -> Query:
    """Get samples by analysis type."""
    return samples.filter(data_analysis in Family.data_analysis)


def get_sample_delivered(samples: Query) -> Query:
    """Get delivered samples."""
    return samples.filter(Sample.delivered_at.isnot(None))


def get_sample_not_delivered(samples: Query) -> Query:
    """Get samples that are not delivered."""
    return samples.filter(Sample.delivered_at.is_(None))


def get_sample_not_invoice_id(samples: Query) -> Query:
    """Get samples that are not attached to an invoice."""
    return samples.filter(Sample.invoice_id.is_(None))


def get_samples_not_down_sampled(samples: Query) -> Query:
    """Get samples that are not down sampled."""
    return samples.filter(Sample.downsampled_to.is_(None))


def get_samples_down_sampled(samples: Query) -> Query:
    """Get samples that are down sampled."""
    return samples.filter(Sample.downsampled_to.isnot(None))


def get_sample_sequenced(samples: Query) -> Query:
    """Get samples that are sequenced."""
    return samples.filter(Sample.sequenced_at.isnot(None))


def get_sample_not_sequenced(samples: Query) -> Query:
    """Get samples that are not sequenced."""
    return samples.filter(Sample.sequenced_at.is_(None))


def get_sample_do_invoice(samples: Query) -> Query:
    """Get samples that should be invoiced."""
    return samples.filrer(Sample.no_invoice.is_(False))


def get_sample_do_not_invoice(samples: Query) -> Query:
    """Get samples marked to skip invoicing."""
    return samples.filrer(Sample.no_invoice.is_(True))


def apply_sample_filter(
    function: str,
    samples: Query,
    internal_id: Optional[str] = None,
    entry_id: Optional[int] = None,
    tissue_type: Optional[SampleType] = None,
    data_analysis: Optional[str] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""
    filter_map = {
        "sample": sample,
        "get_samples_with_type": get_samples_with_type,
        "samples_uploaded_to_loqusdb": get_samples_with_loqusdb_id,
        "samples_not_uploaded_to_loqusdb": get_samples_without_loqusdb_id,
        "get_sample_by_entry_id": get_sample_by_entry_id,
        "get_sample_by_analysis": get_samples_by_analysis,
        "get_sample_delivered": get_sample_delivered,
        "get_sample_not_delivered": get_sample_not_delivered,
        "get_sample_not_invoice_id": get_sample_not_invoice_id,
        "get_sample_down_sampled": get_samples_down_sampled,
        "get_sample_not_down_sampled": get_samples_not_down_sampled,
        "get_sample_sequenced": get_sample_sequenced,
        "get_sample_not_sequenced": get_sample_not_sequenced,
        "get_sample_do_invoice": get_sample_do_invoice,
        "get_sample_do_not_invoice": get_sample_do_not_invoice,
    }
    return filter_map[function](
        samples=samples,
        internal_id=internal_id,
        entry_id=entry_id,
        tissue_type=tissue_type,
        data_analysis=data_analysis,
    )
