# -*- coding: utf-8 -*-
import datetime as dt
import json
from pathlib import Path

import pytest

from cg.store import Store


@pytest.yield_fixture(scope='function')
def store() -> Store:
    _store = Store(uri='sqlite://')
    _store.create_all()
    yield _store
    _store.drop_all()


@pytest.yield_fixture(scope='function')
def base_store(store) -> Store:
    """Setup and example store."""
    customer_group = store.add_customer_group('dummy_group', 'dummy group')
    store.add_commit(customer_group)
    customers = [store.add_customer('cust000', 'Production', scout_access=True,
                                    invoice_address='Test street', customer_group=customer_group),
                 store.add_customer('cust001', 'Customer', scout_access=False, customer_group=customer_group),
                 store.add_customer('cust002', 'Karolinska', scout_access=True, customer_group=customer_group),
                 store.add_customer('cust003', 'CMMS', scout_access=True, customer_group=customer_group)]
    store.add_commit(customers)
    applications = [store.add_application('WGXCUSC000', 'wgs', 'External WGS',
                                          sequencing_depth=0, is_external=True),
                    store.add_application('EXXCUSR000', 'wes', 'External WES',
                                          sequencing_depth=0, is_external=True),
                    store.add_application('WGSPCFC060', 'wgs', 'WGS, double', sequencing_depth=30,
                                          accredited=True),
                    store.add_application('RMLS05R150', 'rml', 'Ready-made', sequencing_depth=0),
                    store.add_application('WGTPCFC030', 'wgs', 'WGS trio', is_accredited=True,
                                          sequencing_depth=30, target_reads=300000000,
                                          limitations='some'),
                    ]
    store.add_commit(applications)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    versions = [store.add_version(application, 1, valid_from=dt.datetime.now(), prices=prices)
                for application in applications]
    store.add_commit(versions)

    yield store


@pytest.fixture(scope='function')
def sample_store(base_store) -> Store:
    """Populate store with samples."""
    new_samples = [
        base_store.add_sample('ordered', sex='male'),
        base_store.add_sample('received', sex='unknown', received=dt.datetime.now()),
        base_store.add_sample('received-prepared', sex='unknown', received=dt.datetime.now(),
                              prepared_at = dt.datetime.now()),
        base_store.add_sample('external', sex='female', external=True),
        base_store.add_sample('external-received', sex='female', external=True,
                              received=dt.datetime.now()),
        base_store.add_sample('sequenced', sex='male', received=dt.datetime.now(),
                              prepared_at=dt.datetime.now(),
                              sequenced_at=dt.datetime.now(), reads=(310 * 1000000)),
        base_store.add_sample('sequenced-partly', sex='male',
                              received=dt.datetime.now(),
                              prepared_at=dt.datetime.now(),
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


@pytest.yield_fixture(scope='function')
def disk_store(cli_runner, invoke_cli) -> Store:
    database = './test_db.sqlite3'
    database_path = Path(database)
    database_uri = f"sqlite:///{database}"
    with cli_runner.isolated_filesystem():
        assert database_path.exists() is False

        # WHEN calling "init"
        result = invoke_cli(['--database', database_uri, 'init'])

        # THEN it should setup the database with some tables
        assert result.exit_code == 0
        assert database_path.exists()
        assert len(Store(database_uri).engine.table_names()) > 0

        yield Store(database_uri)


