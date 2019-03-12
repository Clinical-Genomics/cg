"""Test methods for cg/cli/set/microbial_order"""
from datetime import datetime

from cg.store import Store


def test_invalid_order_empty_db(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN running set with an order that does not exist
    order_id = 'dummy_order_id'
    application_tag = 'dummy_application'
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial-order', order_id,
                         'sign', '-a', application_tag])

    # THEN then it should complain on invalid order
    assert result.exit_code == 1


def test_invalid_order_non_empty_db(invoke_cli, disk_store: Store):
    # GIVEN a non empty database
    add_microbial_order(disk_store)

    # WHEN running set with an order that does not exist
    order_id = 'dummy_order_id'
    application_tag = 'dummy_application'
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial-order', order_id,
                         'sign', '-a', application_tag])

    # THEN then it should complain on invalid order
    assert result.exit_code == 1


def test_valid_order_no_apptag_option(invoke_cli, disk_store: Store):
    # GIVEN a non empty database
    order = add_microbial_order(disk_store)

    # WHEN running set with an order that does not exist
    order_id = order.internal_id
    result = invoke_cli(['--database', disk_store.uri, 'set', 'microbial-order', order_id, 'sign'])

    # THEN then it should just exit
    assert result.exit_code == 1


def ensure_application_version(store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(tag=application_tag, category='wgs',
                                            description='dummy_description')
        store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = store.application_version(application, 1)
    if not version:
        version = store.add_version(application, 1, valid_from=datetime.now(), prices=prices)
        store.add_commit(version)
    return version


def ensure_customer(store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group_id = customer_id + '_group'
    customer_group = store.customer_group(customer_group_id)
    if not customer_group:
        customer_group = store.add_customer_group(customer_group_id, customer_group_id)

        customer = store.add_customer(internal_id=customer_id, name="Test Customer",
                                      scout_access=False, customer_group=customer_group,
                                      invoice_address='dummy_address',
                                      invoice_reference='dummy_reference')
        store.add_commit(customer)
    customer = store.customer(customer_id)
    return customer


def add_organism(store):
    """utility function to add an organism to use in tests"""
    organism = store.add_organism(internal_id='organism_id', name='organism_name')
    return organism


def add_microbial_sample(store, sample_id='sample_test'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version = ensure_application_version(store)
    organism = add_organism(store)
    sample = store.add_microbial_sample(name=sample_id,
                                        organism=organism,
                                        internal_id=sample_id,
                                        reference_genome='test',
                                        application_version=application_version)
    sample.customer = customer
    return sample


def add_microbial_order(store, order_id='order_test', customer_id='cust_test'):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(store, customer_id)
    with store.session.no_autoflush:
        order = store.add_microbial_order(name=order_id, internal_id=order_id, customer=customer,
                                          ordered=datetime.now())
        order.customer = customer
        sample = add_microbial_sample(store)
        order.microbial_samples.append(sample)
    store.add_commit(sample)
    return order
