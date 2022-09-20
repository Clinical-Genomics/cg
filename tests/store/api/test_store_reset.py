"""Tests for reset part of the store API"""
from cg.constants.subject import Gender
from cg.store import Store, models


def test_reset_observation(store: Store, helpers):
    """Test reset observation links."""

    # GIVEN a store with a case with Loqusdb-links
    case: models.Family = helpers.add_case(store)
    sample: models.Sample = helpers.add_sample(store, loqusdb_id=True)
    store.relate_sample(family=case, sample=sample, status=Gender.UNKNOWN)
    assert sample.loqusdb_id is not None

    # WHEN calling reset observations
    store.reset_observations(case=case)

    # THEN the links to observations in loqusdb should have been reset
    assert sample.loqusdb_id is None
