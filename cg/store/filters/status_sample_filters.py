from typing import Optional, List, Callable
from enum import Enum
from sqlalchemy.orm import Query

from cg.constants.constants import SampleType
from cg.store.models import Sample, Customer


def filter_samples_by_internal_id(internal_id: str, samples: Query, **kwargs) -> Query:
    """Return sample by internal id."""
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
    """Return delivered samples."""
    return samples.filter(Sample.delivered_at.isnot(None))


def filter_samples_is_not_delivered(samples: Query, **kwargs) -> Query:
    """Return samples that are not delivered."""
    return samples.filter(Sample.delivered_at.is_(None))


def filter_samples_by_invoice_id(samples: Query, invoice_id: int, **kwargs) -> Query:
    """Return samples by invoice_id"""
    return samples.filter(Sample.invoice_id == invoice_id)


def filter_samples_without_invoice_id(samples: Query, **kwargs) -> Query:
    """Return samples that are not attached to an invoice."""
    return samples.filter(Sample.invoice_id.is_(None))


def filter_samples_is_not_down_sampled(samples: Query, **kwargs) -> Query:
    """Return samples that are not down sampled."""
    return samples.filter(Sample.downsampled_to.is_(None))


def filter_samples_is_down_sampled(samples: Query, **kwargs) -> Query:
    """Return samples that are down sampled."""
    return samples.filter(Sample.downsampled_to.isnot(None))


def filter_samples_is_sequenced(samples: Query, **kwargs) -> Query:
    """Return samples that are sequenced."""
    return samples.filter(Sample.sequenced_at.isnot(None))


def filter_samples_is_not_sequenced(samples: Query, **kwargs) -> Query:
    """Return samples that are not sequenced."""
    return samples.filter(Sample.sequenced_at.is_(None))


def filter_samples_do_invoice(samples: Query, **kwargs) -> Query:
    """Return samples that should be invoiced."""
    return samples.filter(Sample.no_invoice.is_(False))


def filter_samples_do_not_invoice(samples: Query, **kwargs) -> Query:
    """Return samples marked to skip invoicing."""
    return samples.filter(Sample.no_invoice.is_(True))


def filter_samples_by_customer_id(samples: Query, customer_ids: List[int], **kwargs) -> Query:
    """Return samples by customer id."""
    return samples.filter(Sample.customer_id.in_(customer_ids))


def filter_samples_by_customer_name(samples: Query, customer_name: str, **kwargs) -> Query:
    """Return samples by customer name."""
    return samples.filter(Sample.customer_name == customer_name)


def filter_samples_is_received(samples: Query, **kwargs) -> Query:
    """Return samples that are received."""
    return samples.filter(Sample.received_at.isnot(None))


def filter_samples_is_not_received(samples: Query, **kwargs) -> Query:
    """Return samples that are not received."""
    return samples.filter(Sample.received_at.is_(None))


def filter_samples_is_prepared(samples: Query, **kwargs) -> Query:
    """Return samples that are prepared."""
    return samples.filter(Sample.prepared_at.isnot(None))


def filter_samples_is_not_prepared(samples: Query, **kwargs) -> Query:
    """Return samples that are not prepared."""
    return samples.filter(Sample.prepared_at.is_(None))


def filter_samples_by_subject_id(samples: Query, subject_id: str, **kwargs) -> Query:
    """Return samples by subject id."""
    return samples.filter(Sample.subject_id == subject_id)


def filter_samples_is_tumour(samples: Query, **kwargs) -> Query:
    """Return samples that are tumour."""
    return samples.filter(Sample.is_tumour.is_(True))


def filter_samples_is_not_tumour(samples: Query, **kwargs) -> Query:
    """Return samples that are not tumour."""
    return samples.filter(Sample.is_tumour.is_(False))


def filter_samples_by_name_pattern(samples: Query, name_pattern: str, **kwargs) -> Query:
    """Return samples matching the name pattern."""
    filtered_samples = samples.filter(Sample.name.like(f"%{name_pattern}%"))
    return filtered_samples if filtered_samples.all() else samples


def filter_samples_by_customer(samples: Query, customer: Customer, **kwargs) -> Query:
    """Return samples by customer."""
    return samples.filter(Sample.customer == customer)


def apply_sample_filter(
    filter_functions: List[Callable],
    samples: Query,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    tissue_type: Optional[SampleType] = None,
    data_analysis: Optional[str] = None,
    invoice_id: Optional[int] = None,
    customer_ids: Optional[List[int]] = None,
    subject_id: Optional[str] = None,
    name: Optional[str] = None,
    customer: Optional[Customer] = None,
    name_pattern: Optional[str] = None,
) -> Query:
    """Apply filtering functions to the sample queries and return filtered results."""

    for filter_function in filter_functions:
        samples: Query = filter_function(
            samples=samples,
            entry_id=entry_id,
            internal_id=internal_id,
            tissue_type=tissue_type,
            data_analysis=data_analysis,
            invoice_id=invoice_id,
            customer_ids=customer_ids,
            subject_id=subject_id,
            name=name,
            customer=customer,
            name_pattern=name_pattern,
        )
    return samples


class SampleFilter(Enum):
    """Define Sample filter functions."""

    FILTER_BY_INTERNAL_ID: Callable = filter_samples_by_internal_id
    FILTER_WITH_TYPE: Callable = filter_samples_with_type
    FILTER_WITH_LOQUSDB_ID: Callable = filter_samples_with_loqusdb_id
    FILTER_WITHOUT_LOQUSDB_ID: Callable = filter_samples_without_loqusdb_id
    FILTER_BY_ENTRY_ID: Callable = filter_samples_by_entry_id
    FILTER_IS_DELIVERED: Callable = filter_samples_is_delivered
    FILTER_IS_NOT_DELIVERED: Callable = filter_samples_is_not_delivered
    FILTER_BY_INVOICE_ID: Callable = filter_samples_by_invoice_id
    FILTER_HAS_NO_INVOICE_ID: Callable = filter_samples_without_invoice_id
    FILTER_IS_NOT_DOWN_SAMPLED: Callable = filter_samples_is_not_down_sampled
    FILTER_IS_DOWN_SAMPLED: Callable = filter_samples_is_down_sampled
    FILTER_IS_SEQUENCED: Callable = filter_samples_is_sequenced
    FILTER_IS_NOT_SEQUENCED: Callable = filter_samples_is_not_sequenced
    FILTER_DO_INVOICE: Callable = filter_samples_do_invoice
    FILTER_DO_NOT_INVOICE: Callable = filter_samples_do_not_invoice
    FILTER_BY_CUSTOMER_NAME: Callable = filter_samples_by_customer_name
    FILTER_BY_CUSTOMER_ID: Callable = filter_samples_by_customer_id
    FILTER_IS_RECEIVED: Callable = filter_samples_is_received
    FILTER_IS_NOT_RECEIVED: Callable = filter_samples_is_not_received
    FILTER_IS_PREPARED: Callable = filter_samples_is_prepared
    FILTER_IS_NOT_PREPARED: Callable = filter_samples_is_not_prepared
    FILTER_BY_SAMPLE_NAME: Callable = filter_samples_by_name
    FILTER_BY_SUBJECT_ID: Callable = filter_samples_by_subject_id
    FILTER_IS_TUMOUR: Callable = filter_samples_is_tumour
    FILTER_IS_NOT_TUMOUR: Callable = filter_samples_is_not_tumour
    FILTER_BY_NAME_PATTERN: Callable = filter_samples_by_name_pattern
    FILTER_BY_CUSTOMER: Callable = filter_samples_by_customer
