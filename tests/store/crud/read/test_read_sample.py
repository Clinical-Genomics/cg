"""Tests the find business data part of the Cg store API related to sample model."""

from typing import Any

import pytest
from _pytest.fixtures import FixtureRequest
from sqlalchemy.orm import Query

from cg.constants import PrepCategory
from cg.store.models import Customer, Invoice, Sample
from cg.store.store import Store
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
    customer_ids: list[int] = [1, 2],
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
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_ids_and_subject_id_and_is_tumour(
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
    samples = store_with_samples_customer_id_and_subject_id_and_tumour_status.get_samples_by_customer_ids_and_subject_id_and_is_tumour(
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
    identifiers: dict[str, Any] = {
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
    identifiers: dict[str, str] = {
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


def test_samples_to_receive_external(sample_store: Store, helpers: StoreHelpers):
    """Test fetching external sample."""
    # GIVEN a store with a mixture of samples
    assert len(sample_store._get_query(table=Sample).all()) > 1

    # WHEN finding external samples to receive
    samples: list[Sample] = sample_store.get_samples_to_receive(external=True)

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
                if sample.last_sequenced_at
            ]
        )
        >= 1
    )

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples: list[Sample] = sample_store.get_samples_to_sequence()

    # THEN samples should be a list of samples
    assert isinstance(sequence_samples, list)
    assert isinstance(sequence_samples[0], Sample)

    # THEN it should list the received and partly sequenced samples
    assert len(sequence_samples) == 2
    assert {sample.name for sample in sequence_samples} == set(
        ["sequenced-partly", "received-prepared"]
    )
    for sample in sequence_samples:
        assert sample.last_sequenced_at is None
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
    prepare_samples: list[Sample] = sample_store.get_samples_to_prepare()

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


@pytest.mark.parametrize(
    "object_type, identifier_fixture",
    [
        ("sample", "sample_id_sequenced_on_multiple_flow_cells"),
        ("flow_cell", "novaseq_x_flow_cell_id"),
        ("case", "case_id_for_sample_on_multiple_flow_cells"),
    ],
    ids=["sample", "flow_cell", "case"],
)
def test_get_samples_by_identifier(
    re_sequenced_sample_illumina_data_store: Store,
    object_type: str,
    identifier_fixture: str,
    request: FixtureRequest,
):
    """Test that samples are returned for any instance of an identifier."""
    # GIVEN a store with samples, an identifier and an object type
    store: Store = re_sequenced_sample_illumina_data_store
    identifier: str = request.getfixturevalue(identifier_fixture)

    # WHEN fetching the samples by identifier
    samples: list[Sample] = store.get_samples_by_identifier(
        object_type=object_type, identifier=identifier
    )

    # THEN a list of samples should be returned
    assert isinstance(samples, list)
    assert isinstance(samples[0], Sample)


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
    three_customer_ids: list[str],
):
    """Test that samples to invoice can be returned for a customer."""
    # GIVEN a database with samples for a customer

    # THEN the one customer can be retrieved
    customer: Customer = store_with_samples_for_multiple_customers.get_customer_by_internal_id(
        customer_internal_id=three_customer_ids[1]
    )
    assert customer

    # WHEN getting the samples to invoice for a customer
    samples: list[Sample] = (
        store_with_samples_for_multiple_customers.get_samples_to_invoice_for_customer(
            customer=customer,
        )
    )

    # THEN the samples should be returned
    assert samples
    assert len(samples) == 1

    assert samples[0].customer.internal_id == three_customer_ids[1]


def test_get_samples_by_customer_id_and_pattern_with_collaboration(
    store_with_samples_for_multiple_customers: Store,
    helpers: StoreHelpers,
    three_customer_ids: list[str],
):
    """Test that samples can be returned for a customer."""
    # GIVEN a database with samples for a customer

    # THEN the one customer can be retrieved
    customer: set[Customer] = store_with_samples_for_multiple_customers.get_customer_by_internal_id(
        customer_internal_id=three_customer_ids[1]
    ).collaborators
    assert customer

    # WHEN getting the samples for a customer
    samples: list[Sample] = (
        store_with_samples_for_multiple_customers.get_samples_by_customers_and_pattern(
            customers=customer,
            pattern="sample",
        )
    )

    # THEN the samples should be returned
    assert samples
    assert len(samples) == 3

    for sample in samples:
        assert "sample" in sample.name


def test_get_related_samples(
    store_with_rna_and_dna_samples_and_cases: Store,
    rna_sample: Sample,
    related_dna_samples: list[Sample],
    rna_sample_collaborators: set[Customer],
):
    # GIVEN a database with an RNA sample and several DNA samples with the same subject_id and tumour status as the given sample
    # GIVEN that all customers are in a collaboration
    # GIVEN a list of dna prep categories
    dna_prep_categories: list[PrepCategory] = [
        PrepCategory.WHOLE_GENOME_SEQUENCING,
        PrepCategory.TARGETED_GENOME_SEQUENCING,
        PrepCategory.WHOLE_EXOME_SEQUENCING,
    ]

    # WHEN getting the related DNA samples to the given sample
    fetched_related_dna_samples = store_with_rna_and_dna_samples_and_cases.get_related_samples(
        sample_internal_id=rna_sample.internal_id,
        prep_categories=dna_prep_categories,
        collaborators=rna_sample_collaborators,
    )

    # THEN the correct set of samples is returned
    assert set(related_dna_samples) == set(fetched_related_dna_samples)
