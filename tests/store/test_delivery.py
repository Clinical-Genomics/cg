"""Tests for the samples to deliver api"""

import datetime as dt

from cg.store.models import Sample


def test_list_samples_to_deliver(base_store, helpers):
    """Test to fetch samples ready for delivery"""
    store = base_store
    # GIVEN a populated store without samples
    assert len(store._get_query(table=Sample).all()) == 0
    # GIVEN inserting a sample that should be delivered
    helpers.add_sample(store, last_sequenced_at=dt.datetime.now())
    assert len(store._get_query(table=Sample).all()) == 1

    # WHEN asking for samples to deliver
    samples_to_deliver: list[Sample] = store.get_samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert len(samples_to_deliver) == 1
    assert isinstance(samples_to_deliver[0].last_sequenced_at, dt.datetime)


def test_list_samples_to_deliver_multiple_samples(base_store, helpers):
    """Test to fetch samples ready for delivery and avoid the ones that are not"""
    store = base_store
    # GIVEN a populated store with two samples where one is scheduled for delivery
    helpers.add_sample(store, last_sequenced_at=dt.datetime.now())
    helpers.add_sample(
        store, name="delivered", last_sequenced_at=dt.datetime.now(), delivered_at=dt.datetime.now()
    )
    assert len(store._get_query(table=Sample).all()) == 2

    # WHEN asking for samples to deliver
    samples_to_deliver: list[Sample] = store.get_samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert len(samples_to_deliver) == 1
    assert isinstance(samples_to_deliver[0].last_sequenced_at, dt.datetime)
