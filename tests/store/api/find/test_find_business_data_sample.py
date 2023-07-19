"""Tests the find business data part of the Cg store API related to sample model."""

import pytest
from typing import List, Dict, Any
from sqlalchemy.orm import Query
from cg.store import Store

from cg.store.models import Sample, Invoice, Customer
from tests.store_helpers import StoreHelpers


def test_get_all_pools_and_samples_for_invoice_by_invoice_id(store: Store, helpers: StoreHelpers):
    """Test that all pools and samples for an invoice can be fetched."""

    # GIVEN a database with a pool and a sample
    pool = helpers.ensure_pool(store=store, name="pool_1")
    sample = helpers.add_sample(store=store, name="sample_1")

    # AND an invoice with the pool and sample
    invoice: Invoice = helpers.ensure_invoice(store=store, pools=[pool], samples=[sample])

    # ASSERT that there is an invoice with a pool and a sample
    assert len(invoice.pools) == 1
    assert len(invoice.samples) == 1

    # WHEN fetching all pools and samples for the invoice
    records = store.get_pools_and_samples_for_invoice_by_invoice_id(invoice_id=invoice.id)
    # THEN the pool and sample should be returned
    assert pool in records
    assert sample in records


def test_get_samples_by_customer_and_subject_id_query(
    store_with_samples_subject_id_and_tumour_status: Store,
    cust123: str,
    test_subject: str,
):
    """Test that samples can be fetched by subject id."""
    # GIVEN a database with two samples that have a subject ID but only one is tumour

    # GIVEN that there are two samples in the store
    assert len(store_with_samples_subject_id_and_tumour_status._get_query(table=Sample).all()) == 2

    # GIVEN that there is a customer with the given customer id
    assert store_with_samples_subject_id_and_tumour_status.get_customer_by_internal_id(
        customer_internal_id=cust123
    )

    # WHEN fetching the sample by subject id and customer_id
    samples = store_with_samples_subject_id_and_tumour_status._get_samples_by_customer_and_subject_id_query(
        subject_id=test_subject, customer_internal_id=cust123
    )

    # THEN two samples should be returned
    assert samples.count() == 2
    # THEN the fetched samples have the subject id used for filtering
    assert all(fetched_sample.subject_id == test_subject for fetched_sample in samples.all())


def test_get_samples_by_customer_and_subject_id_query_missing_subject_id(
    store_with_samples_and_tumour_status_missing_subject_id: Store,
    cust123: str,
    test_subject: str,
):
    """Test that samples can be fetched by subject id."""
    # GIVEN a database with two samples that have a subject ID but only one is tumour

    # GIVEN that there are two samples in the store
    assert (
        len(store_with_samples_and_tumour_status_missing_subject_id._get_query(table=Sample).all())
        == 2
    )

    # GIVEN that there is a customer with the given customer id
    assert store_with_samples_and_tumour_status_missing_subject_id.get_customer_by_internal_id(
        customer_internal_id=cust123
    )

    # WHEN fetching the sample by subject id and customer_id
    samples = store_with_samples_and_tumour_status_missing_subject_id._get_samples_by_customer_and_subject_id_query(
        subject_id=test_subject, customer_internal_id=cust123
    )

    # THEN two samples should be returned
    assert samples.count() == 0


def test_get_samples_by_subject_id(
    store_with_samples_subject_id_and_tumour_status: Store,
    cust123: str,
    test_subject: str,
):
    """Test that samples can be fetched by subject id."""
    # GIVEN a database with two samples that have a subject ID but only one is tumour

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_subject_id_and_tumour_status._get_query(table=Sample).all()) == 2

    # ASSERT that there is a customer with the given customer id
    assert store_with_samples_subject_id_and_tumour_status.get_customer_by_internal_id(
        customer_internal_id=cust123
    )

    # WHEN fetching the sample by subject id and customer_id
    samples = (
        store_with_samples_subject_id_and_tumour_status.get_samples_by_customer_and_subject_id(
            subject_id=test_subject, customer_internal_id=cust123
        )
    )

    # THEN two samples should be returned
    assert samples and len(samples) == 2


def test_get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
    store_with_samples_customer_id_and_subject_id_and_tumour_status: Store,
    customer_ids: List[int] = [1, 2],
    subject_id: str = "test_subject",
    is_tumour: bool = True,
):
    """Test that samples can be fetched by customer ID, subject ID, and tumour status."""
    # GIVEN a database with four samples, two with customer ID 1 and two with customer ID 2

    # ASSERT that there are customers with the given customer IDs
    for customer_id in customer_ids:
        assert store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_internal_id(
            customer_internal_id=str(customer_id)
        )

    # WHEN fetching the samples by customer ID list, subject ID, and tumour status
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        customer_ids=customer_ids, subject_id=subject_id, is_tumour=is_tumour
    )

    # THEN two samples should be returned, one for each customer ID, with the specified subject ID and tumour status
    assert isinstance(samples, list)
    assert len(samples) == 2

    for sample in samples:
        assert isinstance(sample, Sample)

    for customer_id, sample in zip(customer_ids, samples):
        assert sample.customer_id == customer_id
        assert sample.subject_id == subject_id
        assert sample.is_tumour == is_tumour


def test_get_samples_by_customer_id_list_and_subject_id_and_is_tumour_with_non_existing_customer_id(
    store_with_samples_customer_id_and_subject_id_and_tumour_status: Store,
):
    """Test that no samples are returned when filtering on non-existing customer ID."""
    # GIVEN a database with four samples, two with customer ID 1 and two with customer ID 2

    # ASSERT that there are no customers with the given customer IDs
    customer_ids = [1, 2, 3]
    for customer_id in customer_ids:
        if customer_id == 3:
            assert (
                store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_internal_id(
                    customer_internal_id=str(customer_id)
                )
                is None
            )
        else:
            assert store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_internal_id(
                customer_internal_id=str(customer_id)
            )

    # WHEN fetching the samples by customer ID list, subject ID, and tumour status
    non_existing_customer_id = [3]
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        customer_ids=non_existing_customer_id, subject_id="test_subject", is_tumour=True
    )

    # THEN no samples should be returned
    assert isinstance(samples, list)
    assert len(samples) == 0


def test_get_sample_by_name(store_with_samples_that_have_names: Store, name="test_sample_1"):
    """Test that samples can be fetched by name."""
    # GIVEN a database with two samples of which one has a name

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_that_have_names._get_query(table=Sample).all()) == 4

    # WHEN fetching the sample by name
    samples: Sample = store_with_samples_that_have_names.get_sample_by_name(name=name)

    # THEN one sample should be returned
    assert samples and samples.name == name


def test_has_active_cases_for_sample_analyze(
    store_with_active_sample_analyze: Store,
    sample_internal_id: str = "test_sample_internal_id",
):
    """Test that a sample is active."""
    # GIVEN a store with an active case

    # THEN the sample should be active
    assert (
        store_with_active_sample_analyze.has_active_cases_for_sample(internal_id=sample_internal_id)
        is True
    )


def test_has_active_cases_for_sample_running(
    store_with_active_sample_running: Store,
    sample_internal_id: str = "test_sample_internal_id",
):
    """Test that a sample is active."""
    # GIVEN a store with an active case

    # THEN the sample should be active
    assert (
        store_with_active_sample_running.has_active_cases_for_sample(internal_id=sample_internal_id)
        is True
    )


def test_get_samples_by_customer_and_name(
    store_with_samples_that_have_names: Store,
    name: str = "test_sample_1",
    customer_id="cust000",
):
    """Test that samples can be fetched by name."""
    # GIVEN a database with samples
    # WHEN getting a customer from the store
    customer: Customer = store_with_samples_that_have_names.get_customer_by_internal_id(
        customer_internal_id=customer_id
    )
    assert customer
    # WHEN fetching the sample by name
    sample: Sample = store_with_samples_that_have_names.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=name
    )

    # THEN one sample should be returned
    assert sample
    assert sample.name == name
    assert sample.customer == customer


def test_get_samples_by_customer_and_name_invalid_customer(
    store_with_samples_that_have_names: Store,
    name: str = "test_sample_1",
    customer_id="unrelated_customer",
):
    """Test that samples can be fetched by name does not return a sample when invalid customer is supplied."""
    # GIVEN a database with two samples

    # WHEN getting a customer from the store
    customer: Customer = store_with_samples_that_have_names.get_customer_by_internal_id(
        customer_internal_id=customer_id
    )
    assert customer
    # WHEN fetching the sample by name
    sample: Sample = store_with_samples_that_have_names.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=name
    )

    # THEN one sample should be returned
    assert not sample


def test_get_samples_by_any_id_not_an_attribute_fails(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    identifiers: Dict[str, Any] = {
        "non-existent-attribute": "not-an-attribute",
        "non-existent-value": "not-a-value",
    },
):
    """Test that using an attribute not from Sample raises an error."""
    # GIVEN a store with samples
    sample_query: Query = store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
        table=Sample
    )
    assert sample_query.count() > 0

    # WHEN trying to filter using an attribute not of Sample
    with pytest.raises(AttributeError) as exc_info:
        store_with_a_sample_that_has_many_attributes_and_one_without.get_samples_by_any_id(
            **identifiers
        )

    # THEN the error message should contain the non-existent-attribute
    assert str(exc_info.value) == "type object 'Sample' has no attribute 'non-existent-attribute'"


def test_get_samples_by_any_id_exclusive_filtering_gives_empty_query(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that using mutually exclusive filtering conditions give an empty query."""
    # GIVEN a store with two samples
    sample_query: Query = store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
        table=Sample
    )
    assert sample_query.count() == 2

    # GIVEN that the samples in the query have different values of two attributes
    sample_1: Sample = sample_query[0]
    sample_2: Sample = sample_query[1]
    assert sample_1.name != sample_2.name
    assert sample_1.is_tumour != sample_2.is_tumour

    # WHEN filtering twice mutually exclusive conditions
    identifiers: Dict[str, str] = {
        "name": sample_1.name,
        "is_tumour": sample_2.is_tumour,
    }
    filtered_query: Query = (
        store_with_a_sample_that_has_many_attributes_and_one_without.get_samples_by_any_id(
            **identifiers
        )
    )

    # THEN the filtered query is empty
    assert filtered_query.count() == 0


def test_get_number_of_reads_for_sample_from_metrics(
    store_with_sequencing_metrics: Store, sample_id: str, expected_total_reads: int
):
    """Test if get_number_of_reads_for_sample_from_metrics function returns correct total reads."""

    # GIVEN a store with multiple samples with sequencing metrics

    # WHEN getting number of reads for a specific sample
    actual_total_reads = (
        store_with_sequencing_metrics.get_number_of_reads_for_sample_passing_q30_threshold(
            sample_internal_id=sample_id, q30_threshold=0
        )
    )

    # THEN it should return correct total reads for the sample
    assert actual_total_reads == expected_total_reads
