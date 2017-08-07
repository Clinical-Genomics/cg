# -*- coding: utf-8 -*-
import datetime as dt

import pytest

from cg.store import Store


@pytest.yield_fixture(scope='function')
def store() -> Store:
    _store = Store(uri='sqlite://')
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope='function')
def base_store(store):
    new_customer = store.add_customer(internal_id='cust001', name='Customer', scout=True)
    store.add_commit(new_customer)
    new_application = store.add_application(tag='WGSPCRC030', category='wgs', description='N/A')
    new_version = store.add_version(version=1, valid=dt.datetime.now(), prices={
        'standard': 10,
        'priority': 20,
        'express': 30,
        'research': 5,
    })
    new_version.application = new_application
    store.add_commit(new_application, new_version)
    yield store
