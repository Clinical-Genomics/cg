from alchy import Query

from cg.constants.subject import PhenotypeStatus
from cg.store.status_sample_filters import (
    get_samples_with_loqusdb_id,
    get_samples_without_loqusdb_id,
)


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
