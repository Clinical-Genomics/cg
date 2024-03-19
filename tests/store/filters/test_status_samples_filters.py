from typing import Any

from sqlalchemy.orm import Query

from cg.constants.constants import SampleType
from cg.constants.subject import PhenotypeStatus, Sex
from cg.store.filters.status_sample_filters import (
    filter_samples_by_entry_customer_ids,
    filter_samples_by_entry_id,
    filter_samples_by_identifier_name_and_value,
    filter_samples_by_internal_id,
    filter_samples_by_internal_id_pattern,
    filter_samples_by_invoice_id,
    filter_samples_by_name,
    filter_samples_by_subject_id,
    filter_samples_do_invoice,
    filter_samples_is_delivered,
    filter_samples_is_not_delivered,
    filter_samples_is_not_down_sampled,
    filter_samples_is_not_prepared,
    filter_samples_is_not_received,
    filter_samples_is_not_sequenced,
    filter_samples_is_prepared,
    filter_samples_is_received,
    filter_samples_is_sequenced,
    filter_samples_with_loqusdb_id,
    filter_samples_with_type,
    filter_samples_without_invoice_id,
    filter_samples_without_loqusdb_id,
)
from cg.store.models import CaseSample, Sample
from cg.store.store import Store
from tests.store.conftest import StoreConstants
from tests.store_helpers import StoreHelpers


def test_get_samples_with_loqusdb_id(helpers, store, sample_store, sample_id, loqusdb_id):
    """Test sample extraction with Loqusdb ID."""

    # GIVEN a sample observations that has been uploaded to Loqusdb
    case = helpers.add_case(store)
    sample = helpers.add_sample(store, loqusdb_id=loqusdb_id)
    sample_not_uploaded = helpers.add_sample(store, internal_id=sample_id)
    link_1: CaseSample = sample_store.relate_sample(
        case=case, sample=sample, status=PhenotypeStatus.UNKNOWN
    )
    link_2: CaseSample = sample_store.relate_sample(
        case=case, sample=sample_not_uploaded, status=PhenotypeStatus.UNKNOWN
    )
    sample_store.session.add_all([link_1, link_2])

    # GIVEN a sample query
    samples: Query = store._get_query(table=Sample)

    # WHEN retrieving the Loqusdb uploaded samples
    uploaded_samples = filter_samples_with_loqusdb_id(samples=samples)

    # THEN the obtained sample should match the expected one
    assert sample in uploaded_samples
    assert sample_not_uploaded not in uploaded_samples


def test_get_samples_without_loqusdb_id(
    helpers: StoreHelpers, sample_store: Store, sample_id, loqusdb_id
):
    """Test sample extraction without Loqusdb ID."""

    # GIVEN a sample observations that has not been uploaded to Loqusdb
    sample = helpers.add_sample(sample_store)
    sample_uploaded = helpers.add_sample(
        store=sample_store, internal_id=sample_id, loqusdb_id=loqusdb_id
    )

    # GIVEN a sample query
    samples: Query = sample_store._get_query(table=Sample)

    # WHEN retrieving the Loqusdb not uploaded samples
    not_uploaded_samples = filter_samples_without_loqusdb_id(samples)

    # THEN the obtained sample should match the expected one
    assert sample in not_uploaded_samples
    assert sample_uploaded not in not_uploaded_samples


def test_filter_samples_is_delivered(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a store with two samples of which one is delivered

    # WHEN getting delivered samples
    samples: Query = filter_samples_is_delivered(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have a delivered at date
    assert samples.all()[0].delivered_at is not None


def test_filter_samples_is_not_delivered(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not delivered."""

    # GIVEN a store with two samples of which one is not delivered

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_is_not_delivered(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should not have a delivered at date
    assert samples.all()[0].delivered_at is None


def test_filter_get_samples_by_invoice_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    invoice_id=StoreConstants.INVOICE_ID_SAMPLE_WITH_ATTRIBUTES.value,
):
    """Test that a sample is returned when there is a sample that has an invoice id."""

    # GIVEN a store with two samples of which one has an invoice id

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_by_invoice_id(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        invoice_id=invoice_id,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the correct invoice id
    assert samples.all()[0].invoice_id == invoice_id


def test_filter_samples_without_invoice_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that has no invoice id."""

    # GIVEN a store with two samples of which one does not have an invoice id

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_without_invoice_id(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should not have an invoice id
    assert samples.all()[0].invoice_id is None


def test_filter_samples_not_down_sampled(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not down sampled."""

    # GIVEN a store with two samples of which one is not sequenced

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_is_not_down_sampled(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should not have a down sampled to value
    assert samples.all()[0].downsampled_to is None


def test_filter_samples_is_sequenced(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not sequenced."""

    # GIVEN a store with two samples of which one is not sequenced

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_is_sequenced(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have a sequenced at date
    assert samples.all()[0].last_sequenced_at is not None


def test_filter_samples_is_not_sequenced(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not sequenced."""

    # GIVEN a store with two samples of which one is not sequenced

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_is_not_sequenced(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should not have a sequenced at date
    assert samples.all()[0].last_sequenced_at is None


def test_filter_samples_do_invoice(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is not a sample that should be invoiced."""

    # GIVEN a  store with two samples of which one is marked to skip invoicing

    # WHEN getting  samples mark to be invoiced
    samples: Query = filter_samples_do_invoice(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have a no invoice indicator that is set to False
    assert samples.all()[0].no_invoice is False


def test_filter_samples_is_received(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is received."""

    # GIVEN a store with two samples of which one is received

    # WHEN getting received samples
    samples: Query = filter_samples_is_received(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have a received at date
    assert samples.all()[0].received_at is not None


def test_filter_samples_is_not_received(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not received."""

    # GIVEN a store that has two samples of which one is not received

    # WHEN getting not received samples
    samples: Query = filter_samples_is_not_received(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should not have a received at date
    assert samples.all()[0].received_at is None


def test_filter_samples_is_prepared(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is prepared."""

    # GIVEN a store that has two samples of which one is prepared

    samples: Query = filter_samples_is_prepared(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have a prepared at date
    assert samples.all()[0].prepared_at is not None


def test_filter_samples_is_not_prepared(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample that is not prepared."""

    # GIVEN a store that has two samples of which one is not prepared

    # WHEN getting not prepared samples
    samples: Query = filter_samples_is_not_prepared(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        )
    )

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have not have a prepared at date
    assert samples.all()[0].prepared_at is None


def test_filter_get_samples_by_internal_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    sample_internal_id: str = StoreConstants.INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES.value,
):
    """Test that a sample is returned when there is a sample with the given id."""

    # GIVEN a store with two samples of which one has the given internal id

    # WHEN getting a sample by id
    samples: Query = filter_samples_by_internal_id(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        internal_id=sample_internal_id,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the internal id
    assert samples.all()[0].internal_id == sample_internal_id


def test_filter_get_samples_by_entry_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    entry_id: int = 1,
):
    """Test that a sample is returned when there is a sample with the given entry id."""

    # GIVEN a store with two samples

    # WHEN getting a sample by id
    samples: Query = filter_samples_by_entry_id(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        entry_id=entry_id,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the correct id
    assert samples.all()[0].id == entry_id


def test_filter_get_samples_with_type(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    name=StoreConstants.NAME_SAMPLE_WITH_ATTRIBUTES.value,
    tissue_type: SampleType = SampleType.TUMOR,
):
    """Test that a sample is returned when there is a sample with the given type."""

    # GIVEN a store with two samples of which one is of the given type

    # WHEN getting a sample by type
    samples: Query = filter_samples_with_type(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        tissue_type=tissue_type,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have is tumour set to true
    assert samples.all()[0].is_tumour is True


def test_filter_get_samples_by_name(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    name=StoreConstants.NAME_SAMPLE_WITH_ATTRIBUTES.value,
):
    """Test that a sample is returned when there is a sample with the given type."""
    # GIVEN a store with two samples that have names

    # WHEN getting a sample by name
    samples: Query = filter_samples_by_name(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        name=name,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the correct name
    assert samples.all()[0].name == name


def test_filter_get_samples_by_subject_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    subject_id: str = StoreConstants.SUBJECT_ID_SAMPLE_WITH_ATTRIBUTES.value,
):
    """Test that a sample is returned when there is a sample with the given subject id."""
    # GIVEN a store with two samples of which one has a subject id

    # WHEN getting a sample by subject id
    samples: Query = filter_samples_by_subject_id(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        subject_id=subject_id,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the correct subject id
    assert samples.all()[0].subject_id == subject_id


def test_filter_get_samples_by_customer_id(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that a sample is returned when there is a sample with the given customer id."""
    # GIVEN a store with samples with different customer ids
    samples: Query = store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
        table=Sample
    )
    customer_id: int = samples.first().customer_id
    assert customer_id != samples.order_by(Sample.customer_id.desc()).first().customer_id

    # WHEN filtering the sample query by customer id
    filtered_query: Query = filter_samples_by_entry_customer_ids(
        samples=samples,
        customer_entry_ids=[customer_id],
    )

    # THEN the result of the filtering is a query
    assert isinstance(filtered_query, Query)

    # THEN the filtered query is not empty
    assert filtered_query.all()

    # THEN the filtered query has fewer elements than the unfiltered query
    assert filtered_query.count() < samples.count()

    # THEN a sample in the filtered query should have the correct customer id
    assert filtered_query.first().customer_id == customer_id


def test_filter_get_samples_by_internal_id_pattern(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
    internal_id_pattern: str = "with_attributes",
):
    """Test that a sample is returned when there is a sample with the given internal id pattern."""
    # GIVEN a store with two samples of which one has a name name pattern

    # WHEN getting a sample by name pattern
    samples: Query = filter_samples_by_internal_id_pattern(
        samples=store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
            table=Sample
        ),
        internal_id_pattern=internal_id_pattern,
    )

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all()

    # THEN samples should contain one sample
    assert len(samples.all()) == 1

    # THEN the sample should have the correct name
    assert samples[0].internal_id == StoreConstants.INTERNAL_ID_SAMPLE_WITH_ATTRIBUTES.value


def test_filter_samples_by_identifier_name_and_value_unique_sample(
    store_with_a_sample_that_has_many_attributes_and_one_without: Store,
):
    """Test that the function filters correctly for any identifier."""
    # GIVEN a store with at least two samples
    sample_query: Query = store_with_a_sample_that_has_many_attributes_and_one_without._get_query(
        table=Sample
    )
    assert sample_query.count() > 1

    # GIVEN a sample in store that has all attributes
    sample: Sample = sample_query.first()

    # WHEN filtering the sample query with every existing attribute of the sample
    identifiers: dict[str, Any] = {
        "age_at_sampling": sample.age_at_sampling,
        "application_version_id": sample.application_version_id,
        "capture_kit": sample.capture_kit,
        "comment": sample.comment,
        "control": sample.control,
        "created_at": sample.created_at,
        "customer_id": sample.customer_id,
        "delivered_at": sample.delivered_at,
        "downsampled_to": sample.downsampled_to,
        "from_sample": sample.from_sample,
        "id": sample.id,
        "internal_id": sample.internal_id,
        "invoice_id": sample.invoice_id,
        "is_tumour": sample.is_tumour,
        "loqusdb_id": sample.loqusdb_id,
        "name": sample.name,
        "no_invoice": sample.no_invoice,
        "order": sample.order,
        "ordered_at": sample.ordered_at,
        "organism_id": sample.organism_id,
        "original_ticket": sample.original_ticket,
        "prepared_at": sample.prepared_at,
        "priority": sample.priority,
        "reads": sample.reads,
        "received_at": sample.received_at,
        "reference_genome": sample.reference_genome,
        "sex": sample.sex,
        "last_sequenced_at": sample.last_sequenced_at,
        "subject_id": sample.subject_id,
    }
    for key, value in identifiers.items():
        filtered_sample_query: Query = filter_samples_by_identifier_name_and_value(
            samples=sample_query,
            identifier_name=key,
            identifier_value=value,
        )
        # THEN the filtered query has at least one element
        assert filtered_sample_query.count() > 0
        # THEN the element in the filtered query is the sample for every attribute
        assert getattr(filtered_sample_query.first(), key) == value


def test_filter_samples_by_identifier_name_and_value_two_samples(sample_store: Store):
    """."""
    # GIVEN a store with more than 2 samples
    sample_query: Query = sample_store._get_query(table=Sample)
    assert sample_query.count() > 2

    # WHEN filtering the females from the sample query using identifiers
    filtered_query: Query = filter_samples_by_identifier_name_and_value(
        samples=sample_query,
        identifier_name="sex",
        identifier_value=Sex.FEMALE,
    )

    # THEN the filtered query has at least two elements
    assert filtered_query.count() > 1

    # THEN all the elements of the filtered query are females
    for sample in filtered_query:
        assert sample.sex == Sex.FEMALE
