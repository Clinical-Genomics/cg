"""Tests for reset part of the store API"""

from datetime import datetime, timedelta

from cg.cg.store import models
from cg.cg.store.api.import_func import prices_are_same, versions_are_same, application_version


def test_prices_are_same_int_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.0
    database_price = 0

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_prices_are_not_same_int_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 1.0
    database_price = 0

    # WHEN calling prices are same
    should_not_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_not_be_same


def test_prices_are_same_float_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.654345
    database_price = 1

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_prices_are_same_float_and_int():
    # GIVEN float price that looks like one in excel
    # GIVEN same price but as it looks when saved in database
    float_price = 0.654345
    database_price = 1

    # WHEN calling prices are same
    should_be_same = prices_are_same(database_price, float_price)

    # THEN prices should be considered same
    assert should_be_same


def test_versions_are_same(raw_version, db_version: models.ApplicationVersion, datemode):
    # GIVEN an excel price row
    # same price row committed to the database

    # WHEN calling versions are same
    should_be_same = versions_are_same(db_version, raw_version, datemode)

    # THEN versions are considered same
    assert should_be_same


def test_versions_are_not_same(raw_version, db_version: models.ApplicationVersion, datemode):
    # GIVEN an excel price row
    # same price row committed to the database but with another valid_from
    db_version.valid_from = datetime.now()

    # WHEN calling versions are same
    should_not_be_same = versions_are_same(db_version, raw_version, datemode)

    # THEN versions are considered same
    assert should_not_be_same


def get_prices(excel_path):
    pass


def price_exist_in_store(price, store):
    prices = get_prices_from_store(store)

    return

def all_prices_exists_in_store(store, excel_path):
    prices = get_prices(excel_path)
    for price in prices:
        if not price_exist_in_store(price, store):
            return False

    return True


def test_application_version(store: Store, excel_path):
    # GIVEN a store with applications
    # and an excel file with prices for those applications
    sign = 'TestSign'

    # WHEN calling versions are same
    application_version(store, excel_path, sign)

    # THEN versions are considered same
    assert all_prices_exists_in_store(store, excel_path)


def ensure_application_version(disk_store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 description='dummy_description')
        disk_store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                         prices=prices)

        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group = disk_store.customer_group('dummy_group')
    if not customer_group:
        customer_group = disk_store.add_customer_group('dummy_group', 'dummy group')

        customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer",
                                           scout_access=False, customer_group=customer_group,
                                           invoice_address='dummy_address',
                                           invoice_reference='dummy_reference')
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_sample(store, sample_name='sample_test', loqusdb_links=False):
    """utility function to add a sample to use in tests"""

    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex='unknown')
    sample.application_version_id = application_version_id
    sample.customer = customer
    if loqusdb_links:
        sample.loqusdb_id = True
    store.add_commit(sample)
    return sample


def ensure_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.panel(panel_id)
    if not panel:
        panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                     version=1.0,
                                     date=datetime.now(), genes=1)
        disk_store.add_commit(panel)
    return panel


def add_family(disk_store, family_id='family_test', customer_id='cust_test', ordered_days_ago=0,
               action=None, priority=None):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    family.ordered_at = datetime.now() - timedelta(days=ordered_days_ago)
    if action:
        family.action = action
    if priority:
        family.priority = priority
    disk_store.add_commit(family)
    return family
