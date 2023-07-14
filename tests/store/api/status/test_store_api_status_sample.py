"""Tests for store API status module related to samples."""


from typing import List
from cg.store import Store
from cg.store.models import Sample, Customer
from tests.store_helpers import StoreHelpers


def test_samples_to_receive_external(sample_store: Store, helpers: StoreHelpers):
    """Test fetching external sample."""
    # GIVEN a store with a mixture of samples
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding external samples to receive
    samples: List[Sample] = sample_store.get_samples_to_receive(external=True)

    # THEN samples should be a list of samples
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)

    # THEN assert that only the external sample is returned
    assert len(samples) == 1

    first_sample = samples[0]
    # THEN assert that the sample is external in database
    assert first_sample.application_version.application.is_external is True
    # THEN assert that the sample is does not have a received at stamp
    assert first_sample.received_at is None


def test_get_samples_to_receive_internal(sample_store):
    """Test fetching internal samples."""
    # GIVEN a store with samples in a mix of states
    assert len(sample_store._get_query(table=Sample).all()) > 1
    assert (
        len(
            [sample for sample in sample_store._get_query(table=Sample).all() if sample.received_at]
        )
        > 1
    )

    # WHEN finding which samples are in queue to receive
    assert len(sample_store.get_samples_to_receive()) == 3
    first_sample = sample_store.get_samples_to_receive()[0]

    # THEN samples should be a sample
    assert isinstance(first_sample, Sample)

    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None


def test_samples_to_sequence(sample_store):
    """Test fetching samples to sequence."""
    # GIVEN a store with sample in a mix of states
    assert len(sample_store._get_query(table=Sample).all()) > 1
    assert (
        len(
            [
                sample
                for sample in sample_store._get_query(table=Sample).all()
                if sample.sequenced_at
            ]
        )
        >= 1
    )

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples: List[Sample] = sample_store.get_samples_to_sequence()

    # THEN samples should be a list of samples
    assert isinstance(sequence_samples, list)
    assert isinstance(sequence_samples[0], Sample)

    # THEN it should list the received and partly sequenced samples
    assert len(sequence_samples) == 2
    assert {sample.name for sample in sequence_samples} == set(
        ["sequenced-partly", "received-prepared"]
    )
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == "sequenced-partly":
            assert sample.reads > 0


def test_samples_to_prepare(sample_store):
    """Test fetching samples to prepare."""
    # GIVEN a store with sample in a mix of states
    assert len(sample_store._get_query(table=Sample).all()) > 1
    assert (
        len(
            [sample for sample in sample_store._get_query(table=Sample).all() if sample.prepared_at]
        )
        >= 1
    )

    # WHEN finding which samples are in queue to be prepared
    prepare_samples: List[Sample] = sample_store.get_samples_to_prepare()

    # THEN samples should be a list of samples
    assert isinstance(prepare_samples, list)
    assert isinstance(prepare_samples[0], Sample)

    # THEN it should list the received sample
    assert len(prepare_samples) == 1
    assert prepare_samples[0].name == "received"


def test_get_sample_by_entry_id(sample_store, entry_id=1):
    """Test fetching a sample by entry id."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding a sample by entry id
    sample: Sample = sample_store.get_sample_by_entry_id(entry_id=entry_id)

    # THEN samples should be a list of samples
    assert isinstance(sample, Sample)

    # THEN it should return the sample
    assert sample.id == entry_id


def test_get_sample_by_internal_id(sample_store, internal_id="test_internal_id"):
    """Test fetching a sample by internal id."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding a sample by internal id
    sample: Sample = sample_store.get_sample_by_internal_id(internal_id=internal_id)

    # THEN samples should be a list of samples
    assert isinstance(sample, Sample)

    # THEN it should return the sample
    assert sample.internal_id == internal_id


def test_get_samples_to_deliver(sample_store):
    """Test fetching samples to deliver."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding samples to deliver
    samples = sample_store.get_samples_to_deliver()

    # THEN samples should be a list of samples
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)

    # THEN it should return the samples that are sequenced but not delivered
    assert len(samples) == 2
    assert {sample.name for sample in samples} == set(["to-deliver", "sequenced"])


def test_get_samples_to_invoice_query(sample_store):
    """Test fetching samples to invoice."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding samples to invoice
    sample = sample_store.get_samples_to_invoice_query().first()

    # THEN samples should be a list of samples
    assert isinstance(sample, Sample)

    # THEN it should return all samples that are not invoiced
    assert sample
    assert sample.name == "delivered"


def test_get_samples_not_invoiced(sample_store):
    """Test getting samples not invoiced."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding samples to invoice
    samples = sample_store.get_samples_not_invoiced()

    # THEN samples should be a list of samples
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)

    # THEN it should return all samples that are not invoiced
    assert len(samples) == len(sample_store._get_query(table=Sample).all())


def test_get_samples_not_down_sampled(sample_store: Store, helpers: StoreHelpers, sample_id: int):
    """Test getting samples not down sampled."""
    # GIVEN a store with a sample
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding samples to invoice
    samples = sample_store.get_samples_not_down_sampled()

    # THEN samples should be a list of samples
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)

    # THEN it should return all samples in the store
    assert len(samples) == len(sample_store._get_query(table=Sample).all())


def test_get_samples_to_invoice_for_customer(
    store_with_samples_for_multiple_customers: Store,
    helpers: StoreHelpers,
    three_customer_ids: List[str],
):
    """Test that samples to invoice can be returned for a customer."""
    # GIVEN a database with samples for a customer

    # THEN the one customer can be retrieved
    customer: Customer = store_with_samples_for_multiple_customers.get_customer_by_internal_id(
        customer_internal_id=three_customer_ids[1]
    )
    assert customer

    # WHEN getting the samples to invoice for a customer
    samples: List[
        Sample
    ] = store_with_samples_for_multiple_customers.get_samples_to_invoice_for_customer(
        customer=customer,
    )

    # THEN the samples should be returned
    assert samples
    assert len(samples) == 1

    assert samples[0].customer.internal_id == three_customer_ids[1]


def test_get_samples_by_customer_id_and_pattern_with_collaboration(
    store_with_samples_for_multiple_customers: Store,
    helpers: StoreHelpers,
    three_customer_ids: List[str],
):
    """Test that samples can be returned for a customer."""
    # GIVEN a database with samples for a customer

    # THEN the one customer can be retrieved
    customer: set[Customer] = store_with_samples_for_multiple_customers.get_customer_by_internal_id(
        customer_internal_id=three_customer_ids[1]
    ).collaborators
    assert customer

    # WHEN getting the samples for a customer
    samples: List[
        Sample
    ] = store_with_samples_for_multiple_customers.get_samples_by_customer_id_and_pattern(
        customers=customer,
        pattern="sample",
    )

    # THEN the samples should be returned
    assert samples
    assert len(samples) == 3

    for sample in samples:
        assert "sample" in sample.name
