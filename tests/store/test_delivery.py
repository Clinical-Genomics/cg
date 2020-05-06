"""Tests for the samples to deliver api"""

import datetime as dt


def test_list_samples_to_deliver(sample_store):
    """Test to fetch samples ready for delivery"""
    store = sample_store
    # GIVEN a populated store with samples
    assert store.samples().count() > 1
    # WHEN asking for samples to deliver
    samples_to_deliver = store.samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert samples_to_deliver.count() == 1
    assert isinstance(samples_to_deliver.first().sequenced_at, dt.datetime)
