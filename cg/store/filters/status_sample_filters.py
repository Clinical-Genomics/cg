from enum import Enum
from typing import Any, Callable, List, Optional

from cg.constants.constants import SampleType
from cg.store.models import Customer, Sample
from sqlalchemy import or_
from sqlalchemy.orm import Query


def filter_samples_by_internal_id(internal_id: str, samples: Query, **kwargs) -> Query:
    """Return sample by internal id."""
    return samples.filter(Sample.internal_id == internal_id)


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
    return samples.filter(Sample.sequenced_at.isnot(None))


def filter_samples_is_not_sequenced(samples: Query, **kwargs) -> Query:
    """Return samples that are not sequenced."""
    return samples.filter(Sample.sequenced_at.is_(None))


def filter_samples_do_invoice(samples: Query, **kwargs) -> Query:
    """Return samples that should be invoiced."""
    return samples.filter(Sample.no_invoice.is_(False))


def filter_samples_by_entry_customer_ids(
    samples: Query, customer_entry_ids: List[int], **kwargs
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


def filter_samples_is_tumour(samples: Query, **kwargs) -> Query:
    """Return samples that are tumour."""
    return samples.filter(Sample.is_tumour.is_(True))


def filter_samples_is_not_tumour(samples: Query, **kwargs) -> Query:
    """Return samples that are not tumour."""
    return samples.filter(Sample.is_tumour.is_(False))


def filter_samples_by_internal_id_pattern(
    samples: Query, internal_id_pattern: str, **kwargs
) -> Query:
    """Return samples matching the internal id pattern."""
    return samples.filter(Sample.internal_id.like(f"%{internal_id_pattern}%"))


def filter_samples_by_internal_id_or_name_search(
    samples: Query, search_pattern: str, **kwargs
) -> Query:
    """Return samples matching the internal id or name search."""
    return samples.filter(
        or_(
            Sample.name.like(f"%{search_pattern}%"),
            Sample.internal_id.like(f"%{search_pattern}%"),
        )
    )


def filter_samples_by_customer(samples: Query, customer: Customer, **kwargs) -> Query:
    """Return samples by customer."""
    return samples.filter(Sample.customer == customer)


def order_samples_by_created_at_desc(samples: Query, **kwargs) -> Query:
    """Return samples ordered by created_at descending."""
    return samples.order_by(Sample.created_at.desc())


def filter_samples_by_identifier_name_and_value(
    samples: Query, identifier_name: str, identifier_value: Any, **kwargs
) -> Query:
    """Filters the sample query by the given identifier name and value."""
    return samples.filter(getattr(Sample, identifier_name) == identifier_value)


def apply_sample_filter(
    filter_functions: List[Callable],
    samples: Query,
    entry_id: Optional[int] = None,
    internal_id: Optional[str] = None,
    tissue_type: Optional[SampleType] = None,
    data_analysis: Optional[str] = None,
    invoice_id: Optional[int] = None,
    customer_entry_ids: Optional[List[int]] = None,
    subject_id: Optional[str] = None,
    name: Optional[str] = None,
    customer: Optional[Customer] = None,
    name_pattern: Optional[str] = None,
    internal_id_pattern: Optional[str] = None,
    search_pattern: Optional[str] = None,
    identifier_name: str = None,
    identifier_value: Any = None,
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
            name_pattern=name_pattern,
            internal_id_pattern=internal_id_pattern,
            search_pattern=search_pattern,
            identifier_name=identifier_name,
            identifier_value=identifier_value,
        )
    return samples


class SampleFilter(Enum):
    """Define Sample filter functions."""

    FILTER_BY_CUSTOMER: Callable = filter_samples_by_customer
    FILTER_BY_CUSTOMER_ENTRY_IDS: Callable = filter_samples_by_entry_customer_ids
    FILTER_BY_ENTRY_ID: Callable = filter_samples_by_entry_id
    FILTER_BY_IDENTIFIER_NAME_AND_VALUE: Callable = filter_samples_by_identifier_name_and_value
    FILTER_BY_INTERNAL_ID: Callable = filter_samples_by_internal_id
    FILTER_BY_INTERNAL_ID_OR_NAME_SEARCH: Callable = filter_samples_by_internal_id_or_name_search
    FILTER_BY_INTERNAL_ID_PATTERN: Callable = filter_samples_by_internal_id_pattern
    FILTER_BY_INVOICE_ID: Callable = filter_samples_by_invoice_id
    FILTER_BY_SAMPLE_NAME: Callable = filter_samples_by_name
    FILTER_BY_SUBJECT_ID: Callable = filter_samples_by_subject_id
    FILTER_DO_INVOICE: Callable = filter_samples_do_invoice
    FILTER_HAS_NO_INVOICE_ID: Callable = filter_samples_without_invoice_id
    FILTER_IS_DELIVERED: Callable = filter_samples_is_delivered
    FILTER_IS_NOT_DELIVERED: Callable = filter_samples_is_not_delivered
    FILTER_IS_NOT_DOWN_SAMPLED: Callable = filter_samples_is_not_down_sampled
    FILTER_IS_PREPARED: Callable = filter_samples_is_prepared
    FILTER_IS_NOT_PREPARED: Callable = filter_samples_is_not_prepared
    FILTER_IS_RECEIVED: Callable = filter_samples_is_received
    FILTER_IS_NOT_RECEIVED: Callable = filter_samples_is_not_received
    FILTER_IS_SEQUENCED: Callable = filter_samples_is_sequenced
    FILTER_IS_NOT_SEQUENCED: Callable = filter_samples_is_not_sequenced
    FILTER_IS_TUMOUR: Callable = filter_samples_is_tumour
    FILTER_IS_NOT_TUMOUR: Callable = filter_samples_is_not_tumour
    FILTER_WITH_LOQUSDB_ID: Callable = filter_samples_with_loqusdb_id
    FILTER_WITHOUT_LOQUSDB_ID: Callable = filter_samples_without_loqusdb_id
    FILTER_WITH_TYPE: Callable = filter_samples_with_type
    ORDER_BY_CREATED_AT_DESC: Callable = order_samples_by_created_at_desc
