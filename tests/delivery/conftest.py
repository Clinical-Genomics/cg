# -*- coding: utf-8 -*-
import datetime as dt
import pytest


@pytest.yield_fixture(scope='function')
def samples_store(base_store):
    """Populate store with samples."""
    customer_obj = base_store.customers().first()
    version_obj = base_store.applications().first().versions[0]
    # delivered
    new_sample = base_store.add_sample(name='delivered', sex='male')
    new_sample.delivered_at = dt.datetime(2017, 6, 5)
    new_sample.customer = customer_obj
    new_sample.application_version = version_obj
    base_store.add(new_sample)
    # ready to deliver
    new_sample = base_store.add_sample(name='sequenced', sex='female')
    new_sample.sequenced_at = dt.datetime(2017, 4, 29)
    new_sample.customer = customer_obj
    new_sample.application_version = version_obj
    base_store.add(new_sample)
    # not ready to deliver
    new_sample = base_store.add_sample(name='not_sequenced', sex='female')
    new_sample.customer = customer_obj
    new_sample.application_version = version_obj
    base_store.add(new_sample)
    base_store.commit()
    yield base_store
