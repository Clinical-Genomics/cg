from typing import Optional, List, Callable
from enum import Enum
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


def get_sample_is_delivered(samples: Query, **kwargs) -> Query:
    """Get delivered samples."""
    return samples.filter(Sample.delivered_at.isnot(None))


def get_sample_is_not_delivered(samples: Query, **kwargs) -> Query:
    """Get samples that are not delivered."""
    return samples.filter(Sample.delivered_at.is_(None))


def get_sample_by_invoice_id(samples: Query, invoice_id: int, **kwargs) -> Query:
    """Get samples by invoice_id"""
    return samples.filter(Sample.invoice_id == invoice_id)


def get_sample_without_invoice_id(samples: Query, **kwargs) -> Query:
    """Get samples that are not attached to an invoice."""
    return samples.filter(Sample.invoice_id.is_(None))


def get_sample_not_down_sampled(samples: Query, **kwargs) -> Query:
    """Get samples that are not down sampled."""
    return samples.filter(Sample.downsampled_to.is_(None))


def get_sample_down_sampled(samples: Query, **kwargs) -> Query:
    """Get samples that are down sampled."""
    return samples.filter(Sample.downsampled_to.isnot(None))


def get_sample_is_sequenced(samples: Query, **kwargs) -> Query:
    """Get samples that are sequenced."""
    return samples.filter(Sample.sequenced_at.isnot(None))


def get_sample_is_not_sequenced(samples: Query, **kwargs) -> Query:
    """Get samples that are not sequenced."""
    return samples.filter(Sample.sequenced_at.is_(None))


def get_sample_do_invoice(samples: Query, **kwargs) -> Query:
    """Get samples that should be invoiced."""
    return samples.filter(Sample.no_invoice.is_(False))


def get_sample_do_not_invoice(samples: Query, **kwargs) -> Query:
    """Get samples marked to skip invoicing."""
    return samples.filter(Sample.no_invoice.is_(True))


def get_sample_by_customer_id(samples: Query, customer_id: str, **kwargs) -> Query:
    """Get samples by customer id."""
    return samples.filter(Sample.customer_id == customer_id)


def get_sample_by_customer_name(samples: Query, customer_name: str, **kwargs) -> Query:
    """Get samples by customer name."""
    return samples.filter(Sample.customer_name == customer_name)


def get_sample_is_received(samples: Query, **kwargs) -> Query:
    """Get samples that are received."""
    return samples.filter(Sample.received_at.isnot(None))


def get_sample_is_not_received(samples: Query, **kwargs) -> Query:
    """Get samples that are not received."""
    return samples.filter(Sample.received_at.is_(None))


def get_sample_is_prepared(samples: Query, **kwargs) -> Query:
    """Get samples that are prepared."""
    return samples.filter(Sample.prepared_at.isnot(None))


def get_sample_is_not_prepared(samples: Query, **kwargs) -> Query:
    """Get samples that are not prepared."""
    return samples.filter(Sample.prepared_at.is_(None))


def apply_sample_filter(
    functions: List[Callable],
    samples: Query,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    tissue_type: Optional[SampleType] = None,
    data_analysis: Optional[str] = None,
    invoice_id: Optional[int] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for function in functions:
        samples: Query = function(
            samples=samples,
            entry_id=entry_id,
            internal_id=internal_id,
            tissue_type=tissue_type,
            data_analysis=data_analysis,
            invoice_id=invoice_id,
        )
    return samples


class SampleFilters(Enum):
    """Enum with all sample filters."""

    get_sample_by_sample_id: Callable = get_sample_by_sample_id
    get_samples_with_type: Callable = get_samples_with_type
    get_samples_with_loqusdb_id: Callable = get_samples_with_loqusdb_id
    get_samples_without_loqusdb_id: Callable = get_samples_without_loqusdb_id
    get_sample_by_entry_id: Callable = get_sample_by_entry_id
    get_sample_is_delivered: Callable = get_sample_is_delivered
    get_sample_is_not_delivered: Callable = get_sample_is_not_delivered
    get_sample_by_invoice_id: Callable = get_sample_by_invoice_id
    get_sample_without_invoice_id: Callable = get_sample_without_invoice_id
    get_sample_not_down_sampled: Callable = get_sample_not_down_sampled
    get_sample_down_sampled: Callable = get_sample_down_sampled
    get_sample_is_sequenced: Callable = get_sample_is_sequenced
    get_sample_is_not_sequenced: Callable = get_sample_is_not_sequenced
    get_sample_do_invoice: Callable = get_sample_do_invoice
    get_sample_do_not_invoice: Callable = get_sample_do_not_invoice
    get_sample_by_customer_name: Callable = get_sample_by_customer_name
    get_sample_by_customer_id: Callable = get_sample_by_customer_id
    get_sample_is_received: Callable = get_sample_is_received
    get_sample_is_not_received: Callable = get_sample_is_not_received
    get_sample_is_prepared: Callable = get_sample_is_prepared
    get_sample_is_not_prepared: Callable = get_sample_is_not_prepared
