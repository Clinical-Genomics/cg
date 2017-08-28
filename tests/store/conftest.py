import datetime as dt

import pytest


@pytest.fixture(scope='function')
def sample_store(base_store):
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample('ordered', sex='male'),
        base_store.add_sample('received', sex='unknown', received=dt.datetime.now()),
        base_store.add_sample('external', sex='female', external=True),
        base_store.add_sample('external-received', sex='female', external=True,
                              received=dt.datetime.now()),
        base_store.add_sample('sequenced', sex='male', received=dt.datetime.now(),
                              sequenced_at=dt.datetime.now(), reads=(310 * 1000000)),
        base_store.add_sample('sequenced-partly', sex='male', received=dt.datetime.now(),
                              reads=(250 * 1000000)),
    ]
    customer = base_store.customers().first()
    external_app = base_store.application('WGXCUSC000').versions[0]
    wgs_app = base_store.application('WGTPCFC030').versions[0]
    for sample in new_samples:
        sample.customer = customer
        sample.application_version = external_app if 'external' in sample.name else wgs_app
    base_store.add_commit(new_samples)
    return base_store


@pytest.fixture(scope='function')
def store_families(base_store):
    """Populate store with families in different states."""
    # just added family
    # family read to be analyzed
    # family partly sequenced
    pass
