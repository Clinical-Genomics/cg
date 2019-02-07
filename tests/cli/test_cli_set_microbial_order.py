"""Test methods for cg/cli/set/microbial_order"""
from datetime import datetime

from cg.store import Store


def test_invalid_order(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN running set with an order that does not exist
    order_id = 'dummy_order_id'
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial_order', order_id, 'sign'])

    # THEN then it should complain on invalid order
    assert result.exit_code == 1


def test_invalid_application(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    order = add_microbial_order(disk_store)
    sample = add_microbial_sample(disk_store)
    sample.order = order
    application_tag = 'dummy_application'
    assert disk_store.MicrobialSample.query.first().application_version.application.tag != \
        application_tag

    # WHEN calling set sample with an invalid application
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial_order', order.internal_id,
                         'sign',
                         '-a', application_tag])

    # THEN then it should complain about missing application instead of setting the value
    assert result.exit_code == 1
    assert disk_store.MicrobialSample.query.first().application_version.application.tag != \
        application_tag


def test_application(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample and two applications
    order = add_microbial_order(disk_store)
    sample = add_microbial_sample(disk_store)
    sample.order = order
    application_tag = ensure_application_version(disk_store, 'another_application').application.tag
    assert disk_store.MicrobialSample.query.first().application_version.application.tag != \
        application_tag

    # WHEN calling set sample with an invalid application
    signature = 'sign'
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial_order', order.internal_id,
                         signature, '-a', application_tag])

    # THEN then the application should have been set
    assert result.exit_code == 0
    assert disk_store.MicrobialSample.query.first().application_version.application.tag == \
        application_tag
    assert signature in disk_store.MicrobialSample.query.first().comment


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
        version = disk_store.add_version(application, 1, valid_from=datetime.now(), prices=prices)
        disk_store.add_commit(version)
    return version


def ensure_customer(disk_store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group_id = customer_id + '_group'
    customer_group = disk_store.customer_group(customer_group_id)
    if not customer_group:
        customer_group = disk_store.add_customer_group(customer_group_id, customer_group_id)

        customer = disk_store.add_customer(internal_id=customer_id, name="Test Customer",
                                           scout_access=False, customer_group=customer_group,
                                           invoice_address='dummy_address',
                                           invoice_reference='dummy_reference')
        disk_store.add_commit(customer)
    customer = disk_store.customer(customer_id)
    return customer


def add_microbial_sample(disk_store, order_id='sample_test', sex='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store).id
    sample = disk_store.add_microbial_sample(name=order_id, sex=sex)
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample


def add_microbial_order(disk_store, order_id='order_test', customer_id='cust_test'):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    order = disk_store.add_microbial_order(name=order_id, customer=customer, ordered=datetime.now())
    order.customer = customer
    disk_store.add_commit(order)
    return order
