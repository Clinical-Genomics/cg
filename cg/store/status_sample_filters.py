from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.constants.constants import SampleType
from cg.store.models import Sample


def filter_samples_by_internal_id(internal_id: str, samples: Query, **kwargs) -> Query:
    """Return sample with sample id."""
    return samples.filter_by(internal_id=internal_id)


def filter_samples_by_name(name: str, samples: Query, **kwargs) -> Query:
    """Return sample with sample name."""
    return samples.filter_by(name=name)


def filter_samples_with_type(samples: Query, tissue_type: SampleType, **kwargs) -> Query:
    """Return samples with sample type."""
    is_tumour: bool = tissue_type == SampleType.TUMOR
    return samples.filter(Sample.is_tumour == is_tumour)


def filter_samples_with_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Return samples with a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.isnot(None))


def filter_samples_without_loqusdb_id(samples: Query, **kwargs) -> Query:
    """Return samples without a loqusdb ID."""
    return samples.filter(Sample.loqusdb_id.is_(None))


def filter_samples_by_entry_id(entry_id: int, samples: Query, **kwargs) -> Query:
    """Return sample with entry id."""
    return samples.filter_by(id=entry_id)


def filter_samples_is_delivered(samples: Query, **kwargs) -> Query:
    """Get delivered samples."""
    return samples.filter(Sample.delivered_at.isnot(None))


def filter_samples_is_not_delivered(samples: Query, **kwargs) -> Query:
    """Get samples that are not delivered."""
    return samples.filter(Sample.delivered_at.is_(None))


def filter_samples_by_invoice_id(samples: Query, invoice_id: int, **kwargs) -> Query:
    """Get samples by invoice_id"""
    return samples.filter(Sample.invoice_id == invoice_id)


def filter_samples_without_invoice_id(samples: Query, **kwargs) -> Query:
    """Get samples that are not attached to an invoice."""
    return samples.filter(Sample.invoice_id.is_(None))


def filter_samples_not_down_sampled(samples: Query, **kwargs) -> Query:
    """Get samples that are not down sampled."""
    return samples.filter(Sample.downsampled_to.is_(None))


def filter_samples_down_sampled(samples: Query, **kwargs) -> Query:
    """Get samples that are down sampled."""
    return samples.filter(Sample.downsampled_to.isnot(None))


def filter_samples_is_sequenced(samples: Query, **kwargs) -> Query:
    """Get samples that are sequenced."""
    return samples.filter(Sample.sequenced_at.isnot(None))


def filter_samples_is_not_sequenced(samples: Query, **kwargs) -> Query:
    """Get samples that are not sequenced."""
    return samples.filter(Sample.sequenced_at.is_(None))


def filter_samples_do_invoice(samples: Query, **kwargs) -> Query:
    """Get samples that should be invoiced."""
    return samples.filter(Sample.no_invoice.is_(False))


def filter_samples_do_not_invoice(samples: Query, **kwargs) -> Query:
    """Get samples marked to skip invoicing."""
    return samples.filter(Sample.no_invoice.is_(True))


def filter_samples_by_customer_id(samples: Query, customer_id: str, **kwargs) -> Query:
    """Get samples by customer id."""
    return samples.filter(Sample.customer_id.in_(customer_id))


def filter_samples_by_customer_name(samples: Query, customer_name: str, **kwargs) -> Query:
    """Get samples by customer name."""
    return samples.filter(Sample.customer_name == customer_name)


def filter_samples_is_received(samples: Query, **kwargs) -> Query:
    """Get samples that are received."""
    return samples.filter(Sample.received_at.isnot(None))


def filter_samples_is_not_received(samples: Query, **kwargs) -> Query:
    """Get samples that are not received."""
    return samples.filter(Sample.received_at.is_(None))


def filter_samples_is_prepared(samples: Query, **kwargs) -> Query:
    """Get samples that are prepared."""
    return samples.filter(Sample.prepared_at.isnot(None))


def filter_samples_is_not_prepared(samples: Query, **kwargs) -> Query:
    """Get samples that are not prepared."""
    return samples.filter(Sample.prepared_at.is_(None))


def filter_samples_by_subject_id(samples: Query, subject_id: str, **kwargs) -> Query:
    """Get samples by subject id."""
    return samples.filter(Sample.subject_id == subject_id)


def filter_samples_is_tumour(samples: Query, **kwargs) -> Query:
    """Get samples that are tumour."""
    return samples.filter(Sample.is_tumour.is_(True))


def filter_samples_is_not_tumour(samples: Query, **kwargs) -> Query:
    """Get samples that are not tumour."""
    return samples.filter(Sample.is_tumour.is_(False))


def apply_sample_filter(
    functions: List[Callable],
    samples: Query,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    tissue_type: Optional[SampleType] = None,
    data_analysis: Optional[str] = None,
    invoice_id: Optional[int] = None,
    customer_id: Optional[str] = None,
    subject_id: Optional[str] = None,
    name: Optional[str] = None,
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
            customer_id=customer_id,
            subject_id=subject_id,
            name=name,
        )
    return samples


class SampleFilters(Enum):
    """Enum with all sample filters."""

    filter_samples_by_internal_id: Callable = filter_samples_by_internal_id
    filter_samples_with_type: Callable = filter_samples_with_type
    filter_samples_with_loqusdb_id: Callable = filter_samples_with_loqusdb_id
    filter_samples_without_loqusdb_id: Callable = filter_samples_without_loqusdb_id
    filter_samples_by_entry_id: Callable = filter_samples_by_entry_id
    filter_samples_is_delivered: Callable = filter_samples_is_delivered
    filter_samples_is_not_delivered: Callable = filter_samples_is_not_delivered
    filter_samples_by_invoice_id: Callable = filter_samples_by_invoice_id
    filter_samples_without_invoice_id: Callable = filter_samples_without_invoice_id
    filter_samples_not_down_sampled: Callable = filter_samples_not_down_sampled
    filter_samples_down_sampled: Callable = filter_samples_down_sampled
    filter_samples_is_sequenced: Callable = filter_samples_is_sequenced
    filter_samples_is_not_sequenced: Callable = filter_samples_is_not_sequenced
    filter_samples_do_invoice: Callable = filter_samples_do_invoice
    filter_samples_do_not_invoice: Callable = filter_samples_do_not_invoice
    filter_samples_by_customer_name: Callable = filter_samples_by_customer_name
    filter_samples_by_customer_id: Callable = filter_samples_by_customer_id
    filter_samples_is_received: Callable = filter_samples_is_received
    filter_samples_is_not_received: Callable = filter_samples_is_not_received
    filter_samples_is_prepared: Callable = filter_samples_is_prepared
    filter_samples_is_not_prepared: Callable = filter_samples_is_not_prepared
    filter_samples_by_name: Callable = filter_samples_by_name
    filter_samples_by_subject_id: Callable = filter_samples_by_subject_id
    filter_samples_is_tumour: Callable = filter_samples_is_tumour
    filter_samples_is_not_tumour: Callable = filter_samples_is_not_tumour
