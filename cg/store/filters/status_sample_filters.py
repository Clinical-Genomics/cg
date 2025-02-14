from enum import Enum
from typing import Any, Callable

from sqlalchemy import or_
from sqlalchemy.orm import Query

from cg.constants.constants import SampleType
from cg.store.models import Customer, Sample


def filter_samples_by_internal_id(internal_id: str, samples: Query, **kwargs) -> Query:
    """Return sample by internal id."""
    return samples.filter(Sample.internal_id == internal_id)


def filter_samples_by_internal_ids(internal_ids: list[str], samples: Query, **kwargs) -> Query:
    """Return sample by internal id."""
    return samples.filter(Sample.internal_id.in_(internal_ids)) if internal_ids else samples


def filter_samples_by_name(name: str, samples: Query, **kwargs) -> Query:
    """Return sample with sample name."""
    return samples.filter(Sample.name == name)


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


def filter_samples_is_sequenced(samples: Query, **kwargs) -> Query:
    """Return samples that are sequenced."""
    return samples.filter(Sample.last_sequenced_at.isnot(None))


def filter_samples_is_not_sequenced(samples: Query, **kwargs) -> Query:
    """Return samples that are not sequenced."""
    return samples.filter(Sample.last_sequenced_at.is_(None))


def filter_samples_do_invoice(samples: Query, **kwargs) -> Query:
    """Return samples that should be invoiced."""
    return samples.filter(Sample.no_invoice.is_(False))


def filter_samples_by_entry_customer_ids(
    samples: Query, customer_entry_ids: list[int], **kwargs
) -> Query:
    """Return samples by customer id."""
    return samples.filter(Sample.customer_id.in_(customer_entry_ids))


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


def filter_samples_on_tumour(samples: Query, is_tumour: bool, **kwargs) -> Query:
    """Return samples on matching tumour status."""
    return samples.filter(Sample.is_tumour.is_(is_tumour))


def filter_samples_by_internal_id_pattern(
    samples: Query, internal_id_pattern: str, **kwargs
) -> Query:
    """Return samples matching the internal id pattern."""
    return samples.filter(Sample.internal_id.contains(internal_id_pattern))


def filter_samples_by_internal_id_or_name_search(
    samples: Query, search_pattern: str | None, **kwargs
) -> Query:
    """Return samples matching the internal id or name search."""
    if search_pattern is None:
        return samples
    return samples.filter(
        or_(
            Sample.name.contains(search_pattern),
            Sample.internal_id.contains(search_pattern),
        )
    )


def filter_samples_by_customer(samples: Query, customer: Customer, **kwargs) -> Query:
    """Return samples by customer."""
    return samples.filter(Sample.customer == customer)


def filter_samples_by_customers(samples: Query, customers: list[Customer], **kwargs) -> Query:
    """Return samples by customers."""
    customer_ids = [customer.id for customer in customers]
    return samples.filter(Sample.customer_id.in_(customer_ids))


def order_samples_by_created_at_desc(samples: Query, **kwargs) -> Query:
    """Return samples ordered by created_at descending."""
    return samples.order_by(Sample.created_at.desc())


def filter_samples_by_identifier_name_and_value(
    samples: Query, identifier_name: str, identifier_value: Any, **kwargs
) -> Query:
    """Filters the sample query by the given identifier name and value."""
    return samples.filter(getattr(Sample, identifier_name) == identifier_value)


def filter_out_cancelled_samples(samples: Query, **kwargs) -> Query:
    return samples.filter(Sample.is_cancelled.is_(False))


def apply_limit(samples: Query, limit: int, **kwargs) -> Query:
    return samples.limit(limit)


def apply_sample_filter(
    filter_functions: list[Callable],
    samples: Query,
    entry_id: int | None = None,
    internal_id: str | None = None,
    tissue_type: SampleType | None = None,
    data_analysis: str | None = None,
    invoice_id: int | None = None,
    customer_entry_ids: list[int] | None = None,
    subject_id: str | None = None,
    name: str | None = None,
    customer: Customer | None = None,
    customers: list[Customer] | None = None,
    name_pattern: str | None = None,
    internal_id_pattern: str | None = None,
    search_pattern: str | None = None,
    identifier_name: str = None,
    identifier_value: Any = None,
    limit: int | None = None,
    is_tumour: bool | None = None,
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
            customer_entry_ids=customer_entry_ids,
            subject_id=subject_id,
            name=name,
            customer=customer,
            customers=customers,
            name_pattern=name_pattern,
            internal_id_pattern=internal_id_pattern,
            search_pattern=search_pattern,
            identifier_name=identifier_name,
            identifier_value=identifier_value,
            limit=limit,
            is_tumour=is_tumour,
        )
    return samples


class SampleFilter(Enum):
    """Define Sample filter functions."""

    BY_CUSTOMER: Callable = filter_samples_by_customer
    BY_CUSTOMERS: Callable = filter_samples_by_customers
    BY_CUSTOMER_ENTRY_IDS: Callable = filter_samples_by_entry_customer_ids
    BY_ENTRY_ID: Callable = filter_samples_by_entry_id
    BY_IDENTIFIER_NAME_AND_VALUE: Callable = filter_samples_by_identifier_name_and_value
    BY_INTERNAL_ID: Callable = filter_samples_by_internal_id
    BY_INTERNAL_IDS: Callable = filter_samples_by_internal_ids
    BY_INTERNAL_ID_OR_NAME_SEARCH: Callable = filter_samples_by_internal_id_or_name_search
    BY_INTERNAL_ID_PATTERN: Callable = filter_samples_by_internal_id_pattern
    BY_INVOICE_ID: Callable = filter_samples_by_invoice_id
    BY_SAMPLE_NAME: Callable = filter_samples_by_name
    BY_SUBJECT_ID: Callable = filter_samples_by_subject_id
    BY_TUMOUR: Callable = filter_samples_on_tumour
    DO_INVOICE: Callable = filter_samples_do_invoice
    HAS_NO_INVOICE_ID: Callable = filter_samples_without_invoice_id
    IS_NOT_CANCELLED: Callable = filter_out_cancelled_samples
    IS_DELIVERED: Callable = filter_samples_is_delivered
    IS_NOT_DELIVERED: Callable = filter_samples_is_not_delivered
    IS_NOT_DOWN_SAMPLED: Callable = filter_samples_is_not_down_sampled
    IS_PREPARED: Callable = filter_samples_is_prepared
    IS_NOT_PREPARED: Callable = filter_samples_is_not_prepared
    IS_RECEIVED: Callable = filter_samples_is_received
    IS_NOT_RECEIVED: Callable = filter_samples_is_not_received
    IS_SEQUENCED: Callable = filter_samples_is_sequenced
    IS_NOT_SEQUENCED: Callable = filter_samples_is_not_sequenced
    LIMIT: Callable = apply_limit
    WITH_LOQUSDB_ID: Callable = filter_samples_with_loqusdb_id
    WITHOUT_LOQUSDB_ID: Callable = filter_samples_without_loqusdb_id
    WITH_TYPE: Callable = filter_samples_with_type
    ORDER_BY_CREATED_AT_DESC: Callable = order_samples_by_created_at_desc
