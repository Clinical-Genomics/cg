from alchy import Query
from typing import List
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.store.models import Sample
from tests.store_helpers import StoreHelpers
from cg.store.status_sample_filters import (
    get_samples_with_loqusdb_id,
    get_samples_without_loqusdb_id,
    get_sample_is_delivered,
    get_sample_is_not_delivered,
    get_sample_without_invoice_id,
    get_sample_down_sampled,
    get_sample_not_down_sampled,
    get_sample_is_sequenced,
    get_sample_is_not_sequenced,
    get_sample_do_invoice,
    get_sample_do_not_invoice,
    get_sample_by_invoice_id,
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
    samples: Query = store.samples()

    # WHEN retrieving the Loqusdb uploaded samples
    uploaded_samples = get_samples_with_loqusdb_id(samples=samples)

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
    samples: Query = store.samples()

    # WHEN retrieving the Loqusdb not uploaded samples
    not_uploaded_samples = get_samples_without_loqusdb_id(samples=samples)

    # THEN the obtained sample should match the expected one
    assert sample in not_uploaded_samples
    assert sample_uploaded not in not_uploaded_samples


def test_get_sample_by_entry_id(sample_store: Store):
    """Test retrieving sample by entry id."""
    # GIVEN a store containing samples
    # WHEN retrieving a sample by its entry id
    sample: Sample = sample_store.get_sample_by_id(entry_id=1)

    # THEN a sample should be returned
    assert sample


def test_get_sample_by_internal_id(
    store_with_multiple_cases_and_samples: Store, sample_id_in_single_case: str
):
    # GIVEN a store containing a sample
    # WHEN retrieving the sample by its internal id
    sample: Sample = store_with_multiple_cases_and_samples.sample(
        internal_id=sample_id_in_single_case
    )

    # THEN it is returned
    assert sample


def test_filter_sample_is_delivered(
    base_store: Store, helpers: StoreHelpers, timestamp_now: datetime
):
    """Test that a sample is returned when there is a delivered sample."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, delivered_at=timestamp_now)

    # GIVEN a cases Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting delivered samples
    samples: List[Query] = list(get_sample_is_delivered(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_is_not_delivered(
    base_store: Store, helpers: StoreHelpers, timestamp_now: None
):
    """Test that a sample is returned when there is a sample that is not delivered."""

    # GIVEN a not delivered sample
    helpers.add_sample(base_store, delivered_at=timestamp_now)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not delivered samples
    samples: List[Query] = list(get_sample_is_not_delivered(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_get_sample_by_invoice_id(base_store: Store, helpers: StoreHelpers, invoice_id=5):
    """Test that a sample is returned when there is a sample with the specified invoice_id."""

    # GIVEN a with an invoice_id
    helpers.add_sample(base_store, invoice_id=invoice_id)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples by invoice_id
    samples: List[Query] = list(get_sample_by_invoice_id(samples=samples, invoice_id=invoice_id))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_without_invoice_id(
    base_store: Store, helpers: StoreHelpers, invoice_id=None
):
    """Test that a sample is returned when there is a sample without invoice_id."""

    # GIVEN a sampled without invoice_id
    helpers.add_sample(base_store, invoice_id=invoice_id)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples without invoice_id
    samples: List[Query] = list(get_sample_without_invoice_id(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_down_sampled(base_store: Store, helpers: StoreHelpers, timestamp_now: None):
    """Test that a sample is returned when there is a sample that is down sampled."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, downsampled_to=5)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not samples that are down sampled
    samples: List[Query] = list(get_sample_down_sampled(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_not_down_sampled(
    base_store: Store, helpers: StoreHelpers, timestamp_now: None
):
    """Test that a sample is returned when there is a sample that is down sampled."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, downsampled_to=None)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not samples that are not down sampled
    samples: List[Query] = list(get_sample_not_down_sampled(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_is_sequenced(base_store: Store, helpers: StoreHelpers, timestamp_now: None):
    """Test that a sample is returned when there is a sample that is sequenced."""

    # GIVEN a delivered sample
    helpers.add_sample(base_store, sequenced_at=datetime.now())

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting sequenced samples
    samples: List[Query] = list(get_sample_is_sequenced(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_is_not_sequenced(
    base_store: Store, helpers: StoreHelpers, timestamp_now: None
):
    """Test that a sample is returned when there is a sample that is not sequenced."""

    # GIVEN a sample that is not sequenced
    helpers.add_sample(base_store, sequenced_at=None)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting not sequenced samples
    samples: List[Query] = list(get_sample_is_not_sequenced(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_do_invoice(base_store: Store, helpers: StoreHelpers, timestamp_now: None):
    """Test that a sample is returned when there is not a sample that should be invoiced."""

    # GIVEN a samples marked to be invoiced
    helpers.add_sample(base_store, no_invoice=False)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting  samples mark to be invoiced
    samples: List[Query] = list(get_sample_do_invoice(samples=samples))

    # THEN samples should contain the test sample
    assert samples


def test_filter_sample_do_not_invoice(
    base_store: Store, helpers: StoreHelpers, timestamp_now: None
):
    """Test that a sample is returned when there is not a sample that should be invoiced."""

    # GIVEN a  sample marked to skip invoicing
    helpers.add_sample(base_store, no_invoice=True)

    # GIVEN a sample Query
    samples: Query = base_store._get_sample_query()

    # WHEN getting samples that are marked to skip invoicing
    samples: List[Query] = list(get_sample_do_not_invoice(samples=samples))

    # THEN samples should contain the test sample
    assert samples
