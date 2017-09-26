# -*- coding: utf-8 -*-
import datetime as dt


def test_list_samples_to_deliver(samples_store):
    # GIVEN store contains samples in different states
    assert samples_store.samples().count() > 1
    # WHEN asking for samples to deliver
    samples_to_deliver = samples_store.samples_to_deliver()
    # THEN it should return the sample which is ready to deliver
    assert samples_to_deliver.count() == 1
    assert isinstance(samples_to_deliver.first().sequenced_at, dt.datetime)
