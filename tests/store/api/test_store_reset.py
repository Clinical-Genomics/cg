"""Tests for reset part of the store API"""
from cg.store import Store


def test_reset_observation(store: Store, helpers):
    # GIVEN a store with a case with loqus-links
    case = helpers.add_case(store)
    sample = helpers.add_sample(store, loqusdb_id=True)
    store.relate_sample(family=case, sample=sample, status="unknown")
    assert sample.loqusdb_id is not None

    # WHEN calling reset observations
    store.reset_observations(case_id=case.internal_id)

    # THEN the links to observations in loqusdb should have been reset
    assert sample.loqusdb_id is None
