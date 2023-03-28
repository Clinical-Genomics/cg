"""Tests the findbusinessdata part of the Cg store API related to sample model."""

from typing import List
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


def test_get_samples_by_subject_id(
    store_with_samples_subject_id_and_tumour_status: Store,
    helpers: StoreHelpers,
    customer_id: str = "cust123",
    subject_id: str = "test_subject",
):
    """Test that samples can be fetched by subject id."""
    # GIVEN a database with two samples that have a subject ID but only one is tumour

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_subject_id_and_tumour_status.get_samples()) == 2

    # ASSERT that there is a customer with the given customer id
    assert store_with_samples_subject_id_and_tumour_status.get_customer_by_customer_id(
        customer_id=customer_id
    )

    # WHEN fetching the sample by subject id and customer_id
    samples = store_with_samples_subject_id_and_tumour_status.get_samples_by_subject_id(
        subject_id=subject_id, customer_id=customer_id
    )

    # THEN two samples should be returned
    assert samples and len(samples) == 2


def test_get_samples_by_subject_id_and_is_tumour(
    store_with_samples_subject_id_and_tumour_status: Store,
    helpers: StoreHelpers,
    customer_id: str = "cust123",
    subject_id: str = "test_subject",
    is_tumour: bool = True,
):
    """Test that samples can be fetched by subject id."""
    # GIVEN a database with two samples that have a subject ID but only one is tumour

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_subject_id_and_tumour_status.get_samples()) == 2

    # ASSERT that there is a customer with the given customer id
    assert store_with_samples_subject_id_and_tumour_status.get_customer_by_customer_id(
        customer_id=customer_id
    )
    # WHEN fetching the sample by subject id and customer_id
    samples: List[
        Sample
    ] = store_with_samples_subject_id_and_tumour_status.get_samples_by_subject_id_and_is_tumour(
        subject_id=subject_id, customer_id=customer_id, is_tumour=is_tumour
    )

    # THEN two samples should be returned
    assert samples and len(samples) == 1


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
        assert store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_customer_id(
            customer_id=str(customer_id)
        )

    # WHEN fetching the samples by customer ID list, subject ID, and tumour status
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        customer_ids=customer_ids, subject_id=subject_id
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
    helpers: StoreHelpers,
):
    """Test that no samples are returned when filtering on non-existing customer ID."""
    # GIVEN a database with four samples, two with customer ID 1 and two with customer ID 2

    # ASSERT that there are no customers with the given customer IDs
    customer_ids = [1, 2, 3]
    for customer_id in customer_ids:
        if customer_id == 3:
            assert (
                store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_customer_id(
                    customer_id=str(customer_id)
                )
                is None
            )
        else:
            assert store_with_samples_customer_id_and_subject_id_and_tumour_status.get_customer_by_customer_id(
                customer_id=str(customer_id)
            )

    # WHEN fetching the samples by customer ID list, subject ID, and tumour status
    non_existing_customer_id = [3]
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_id_list_and_subject_id_and_is_tumour(
        customer_ids=non_existing_customer_id, subject_id="test_subject"
    )

    # THEN no samples should be returned
    assert isinstance(samples, list)
    assert len(samples) == 0


def test_get_sample_by_name(store_with_samples_that_have_names: Store, name="test_sample_1"):
    """Test that samples can be fetched by name."""
    # GIVEN a database with two samples of which one has a name

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_that_have_names.get_samples()) == 4

    # WHEN fetching the sample by name
    samples: Sample = store_with_samples_that_have_names.get_sample_by_name(name=name)

    # THEN one sample should be returned
    assert samples and samples.name == name


def test_get_samples_by_name_pattern(
    store_with_samples_that_have_names: Store, name_pattern="sample"
):
    """Test that samples can be fetched by name."""
    # GIVEN a database with two samples of which one has a name

    # ASSERT that there are two samples in the store
    assert len(store_with_samples_that_have_names.get_samples()) == 4

    # WHEN fetching the sample by name
    samples: List[Sample] = store_with_samples_that_have_names.get_samples_by_name_pattern(
        name_pattern=name_pattern
    )

    # THEN one sample should be returned
    assert samples and len(samples) == 3


def test_has_active_cases_for_sample_analyze(
    store_with_active_sample_analyze: Store,
    helpers: StoreHelpers,
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
    helpers: StoreHelpers,
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
    helpers: StoreHelpers,
    name: str = "test_sample_1",
    customer_id="cust000",
):
    """Test that samples can be fetched by name."""
    # GIVEN a database with samples
    # WHEN getting a customer from the store
    customer: Customer = store_with_samples_that_have_names.get_customer_by_customer_id(
        customer_id=customer_id
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
    helpers: StoreHelpers,
    name: str = "test_sample_1",
    customer_id="unrelated_customer",
):
    """Test that samples can be fetched by name does not return a sample when invalid customer is supplied."""
    # GIVEN a database with two samples

    # WHEN getting a customer from the store
    customer: Customer = store_with_samples_that_have_names.get_customer_by_customer_id(
        customer_id=customer_id
    )
    assert customer
    # WHEN fetching the sample by name
    sample: Sample = store_with_samples_that_have_names.get_sample_by_customer_and_name(
        customer_entry_id=[customer.id], sample_name=name
    )

    # THEN one sample should be returned
    assert not sample
