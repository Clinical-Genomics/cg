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
    """Setup and example store."""
    customers = [store.add_customer('cust000', 'Production', scout=False),
                 store.add_customer('cust001', 'Customer', scout=False),
                 store.add_customer('cust002', 'Karolinska', scout=True),
                 store.add_customer('cust003', 'CMMS', scout=True)]
    store.add_commit(customers)

    applications = [store.add_application('WGXCUSC000', 'wgs', 'External WGS'),
                    store.add_application('EXXCUSR000', 'wes', 'External WES'),
                    store.add_application('WGSPCFC060', 'wgs', 'WGS, double', accredited=True),
                    store.add_application('RMLS05R150', 'rml', 'Ready-made'),
                    store.add_application('WGTPCFC030', 'wgs', 'WGS trio', accredited=True)]
    store.add_commit(applications)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    versions = [store.add_version(application, 1, valid=dt.datetime.now(), prices=prices)
                for application in applications]
    store.add_commit(versions)

    yield store
