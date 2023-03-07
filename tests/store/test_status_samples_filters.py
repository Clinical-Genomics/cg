from alchy import Query
from typing import List
from cg.constants.subject import PhenotypeStatus
from cg.constants.constants import SampleType
from cg.store import Store
from cg.store.models import Sample
from tests.store_helpers import StoreHelpers
from cg.store.status_sample_filters import (
    filter_samples_with_loqusdb_id,
    filter_samples_without_loqusdb_id,
    filter_samples_is_delivered,
    filter_samples_is_not_delivered,
    filter_samples_without_invoice_id,
    filter_samples_down_sampled,
    filter_samples_not_down_sampled,
    filter_samples_is_sequenced,
    filter_samples_is_not_sequenced,
    filter_samples_do_invoice,
    filter_samples_do_not_invoice,
    filter_samples_by_invoice_id,
    filter_samples_by_internal_id,
    filter_samples_by_entry_id,
    filter_samples_with_type,
    filter_samples_is_prepared,
    filter_samples_is_not_prepared,
    filter_samples_is_received,
    filter_samples_is_not_received,
    filter_samples_by_name,
    filter_samples_by_subject_id,
)
from datetime import datetime


def test_get_samples_with_loqusdb_id(helpers, store, sample_store, sample_id, loqusdb_id):
    """Test sample extraction with Loqusdb ID."""

    # GIVEN a sample observations that has been uploaded to Loqusdb
    case = helpers.add_case(store)
    sample = helpers.add_sample(store, loqusdb_id=loqusdb_id)
    sample_not_uploaded = helpers.add_sample(store, internal_id=sample_id)
    sample_store.relate_sample(family=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    sample_store.relate_sample(
        family=case, sample=sample_not_uploaded, status=PhenotypeStatus.UNKNOWN
    )

    # GIVEN a sample query
    samples: Query = store._get_sample_query()

    # WHEN retrieving the Loqusdb uploaded samples
    uploaded_samples = filter_samples_with_loqusdb_id(samples=samples)

    # THEN the obtained sample should match the expected one
    assert sample in uploaded_samples
    assert sample_not_uploaded not in uploaded_samples


def test_get_samples_without_loqusdb_id(helpers, store, sample_store, sample_id, loqusdb_id):
    """Test sample extraction without Loqusdb ID."""

    # GIVEN a sample observations that has not been uploaded to Loqusdb
    case = helpers.add_case(store)
    sample = helpers.add_sample(store)
    sample_uploaded = helpers.add_sample(store, internal_id=sample_id, loqusdb_id=loqusdb_id)
    sample_store.relate_sample(family=case, sample=sample, status=PhenotypeStatus.UNKNOWN)
    sample_store.relate_sample(family=case, sample=sample_uploaded, status=PhenotypeStatus.UNKNOWN)

    # GIVEN a sample query
    samples: Query = store._get_sample_query()

    # WHEN retrieving the Loqusdb not uploaded samples
    not_uploaded_samples = filter_samples_without_loqusdb_id(samples=samples)

    # THEN the obtained sample should match the expected one
    assert sample in not_uploaded_samples
    assert sample_uploaded not in not_uploaded_samples


def test_get_sample_by_entry_id(sample_store: Store):
    """Test retrieving sample by entry id."""
    # GIVEN a store containing samples
    # WHEN retrieving a sample by its entry id
    sample: Sample = sample_store.get_sample_by_entry_id(entry_id=1)

    # THEN a sample should be returned
    assert sample


def test_get_samples_by_internal_id(
    store_with_multiple_cases_and_samples: Store, sample_id_in_single_case: str
):
    # GIVEN a store containing a sample
    # WHEN retrieving the sample by its internal id
    sample: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        internal_id=sample_id_in_single_case
    )

    # THEN it is returned
    assert sample


def test_filter_samples_is_delivered(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, delivered_at=timestamp_now)
    helpers.add_sample(base_store, delivered_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a cases Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting delivered samples
    samples: Query = filter_samples_is_delivered(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_not_delivered(
    base_store: Store,
    helpers: StoreHelpers,
    timestamp_now: datetime.now(),
):
    """Test that a sample is returned when there is a sample that is not delivered."""

    helpers.add_sample(base_store, delivered_at=timestamp_now)
    helpers.add_sample(base_store, delivered_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2
    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not delivered samples
    samples: List[Sample] = filter_samples_is_not_delivered(samples=samples)

    # THEN samples should contain the test sample
    assert samples and len(samples) == 1


def test_filter_get_samples_by_invoice_id(base_store: Store, helpers: StoreHelpers, invoice_id=5):
    """Test that a sample is returned when there is a sample with the specified invoice_id."""

    # GIVEN a with an invoice_id
    helpers.add_sample(base_store, invoice_id=invoice_id)
    helpers.add_sample(base_store, invoice_id=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples by invoice_id
    samples: Query = filter_samples_by_invoice_id(samples=samples, invoice_id=invoice_id)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_without_invoice_id(base_store: Store, helpers: StoreHelpers, invoice_id=5):
    """Test that a sample is returned when there is a sample without invoice_id."""

    # GIVEN a sampled without invoice_id
    helpers.add_sample(base_store, invoice_id=invoice_id)
    helpers.add_sample(base_store, invoice_id=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples without invoice_id
    samples: Query = filter_samples_without_invoice_id(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_down_sampled(base_store: Store, helpers: StoreHelpers, down_sampled_to=5):
    """Test that a sample is returned when there is a sample that is down sampled."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, downsampled_to=down_sampled_to)
    helpers.add_sample(base_store, downsampled_to=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not samples that are down sampled
    samples: Query = filter_samples_down_sampled(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_not_down_sampled(
    base_store: Store, helpers: StoreHelpers, down_sampled_to=5
):
    """Test that a sample is returned when there is a sample that is down sampled."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, downsampled_to=down_sampled_to)
    helpers.add_sample(base_store, downsampled_to=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not samples that are not down sampled
    samples: Query = filter_samples_not_down_sampled(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_sequenced(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is sequenced."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, sequenced_at=datetime.now())
    helpers.add_sample(base_store, sequenced_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting sequenced samples
    samples: Query = filter_samples_is_sequenced(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_not_sequenced(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is not sequenced."""

    # GIVEN a sample that is not sequenced
    helpers.add_sample(base_store, sequenced_at=None)
    helpers.add_sample(base_store, sequenced_at=datetime.now())

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not sequenced samples
    samples: Query = filter_samples_is_not_sequenced(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_do_invoice(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is not a sample that should be invoiced."""

    # GIVEN a samples marked to be invoiced
    helpers.add_sample(base_store, no_invoice=False)
    helpers.add_sample(base_store, no_invoice=True)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting  samples mark to be invoiced
    samples: Query = filter_samples_do_invoice(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_do_not_invoice(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is not a sample that should be invoiced."""

    # GIVEN a  sample marked to skip invoicing
    helpers.add_sample(base_store, no_invoice=True)
    helpers.add_sample(base_store, no_invoice=False)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples that are marked to skip invoicing
    samples: Query = filter_samples_do_not_invoice(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_delivered(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is delivered."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, delivered_at=datetime.now())
    helpers.add_sample(base_store, delivered_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting delivered samples
    samples: Query = filter_samples_is_delivered(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_not_delivered(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is not delivered."""

    # GIVEN a sample that is not delivered
    helpers.add_sample(base_store, delivered_at=None)
    helpers.add_sample(base_store, delivered_at=datetime.now())

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not delivered samples
    samples: Query = filter_samples_is_not_delivered(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_received(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is received."""

    # GIVEN a received sample
    helpers.add_sample(base_store, received_at=datetime.now())
    helpers.add_sample(base_store, received_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting received samples
    samples: Query = filter_samples_is_received(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_not_received(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is not received."""

    # GIVEN a sample that is not received
    helpers.add_sample(base_store, received_at=None)
    helpers.add_sample(base_store, received_at=datetime.now())

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not received samples
    samples: Query = filter_samples_is_not_received(samples=samples)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_prepared(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is prepared."""

    # GIVEN a prepared sample
    helpers.add_sample(base_store, prepared_at=datetime.now())
    helpers.add_sample(base_store, prepared_at=None)

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting prepared samples
    samples: Query = filter_samples_is_prepared(samples=samples)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_samples_is_not_prepared(base_store: Store, helpers: StoreHelpers):
    """Test that a sample is returned when there is a sample that is not prepared."""

    # GIVEN a sample that is not prepared
    helpers.add_sample(base_store, prepared_at=None)
    helpers.add_sample(base_store, prepared_at=datetime.now())

    # Assert that there are two samples in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not prepared samples
    samples: Query = filter_samples_is_not_prepared(samples=samples)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_get_samples_by_sample_id(
    base_store: Store, helpers: StoreHelpers, sample_id: str = "test_sample_id"
):
    """Test that a sample is returned when there is a sample with the given id."""

    # GIVEN a sample
    helpers.add_sample(base_store, internal_id=sample_id)
    helpers.add_sample(base_store, internal_id=None)

    # Assert that there is one sample in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting a sample by id
    samples: Query = filter_samples_by_internal_id(samples=samples, internal_id=sample_id)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_get_samples_by_entry_id(base_store: Store, helpers: StoreHelpers, entry_id: id = 1):
    """Test that a sample is returned when there is a sample with the given id."""

    # GIVEN a sample
    helpers.add_sample(base_store, id=entry_id)
    helpers.add_sample(base_store, id=None)

    # Assert that there is one sample in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting a sample by id
    samples: Query = filter_samples_by_entry_id(samples=samples, entry_id=entry_id)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_get_samples_with_type(
    base_store: Store,
    helpers: StoreHelpers,
    is_tumour: bool = True,
    tissue_type: SampleType = SampleType.TUMOR,
):
    """Test that a sample is returned when there is a sample with the given type."""

    # GIVEN a sample
    helpers.add_sample(base_store, is_tumour=is_tumour, name="test_tumour")
    helpers.add_sample(base_store, is_tumour=False, name="test_normal")

    # Assert that there is one sample in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting a sample by type
    samples: Query = filter_samples_with_type(samples=samples, tissue_type=tissue_type)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_get_samples_by_name(
    base_store: Store,
    helpers: StoreHelpers,
    is_tumour: bool = True,
):
    """Test that a sample is returned when there is a sample with the given type."""

    # GIVEN a sample
    helpers.add_sample(base_store, is_tumour=is_tumour, name="test_tumour")
    helpers.add_sample(base_store, is_tumour=False, name="test_normal")

    # Assert that there is one sample in the database
    assert len(base_store.get_all_samples()) == 2

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting a sample by type
    samples: Query = filter_samples_by_name(samples=samples, name="test_tumour")

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1


def test_filter_get_samples_by_subject_id(
    base_store: Store, helpers: StoreHelpers, subject_id: str = "test_subject_id"
):
    """Test that a sample is returned when there is a sample with the given subject id."""

    helpers.add_sample(base_store, subject_id=subject_id)
    helpers.add_sample(base_store, subject_id=None)

    # GIVEN a sample query
    samples: Query = base_store._get_sample_query()

    # WHEN getting a sample by subject id
    samples: Query = filter_samples_by_subject_id(samples=samples, subject_id=subject_id)

    # ASSERT that samples is a query
    assert isinstance(samples, Query)

    # THEN samples should contain the test sample
    assert samples.all() and len(samples.all()) == 1
