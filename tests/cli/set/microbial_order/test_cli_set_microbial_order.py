"""Test methods for cg/cli/set/microbial_order"""
from datetime import datetime

import pytest
from cg.cli.set import microbial_order
from cg.store import Store


SUCCESS = 0


def test_invalid_order_empty_db(cli_runner, base_context, base_store: Store):
    # GIVEN an empty database

    # WHEN running set with an order that does not exist
    order_id = 'dummy_order_id'
    application_tag = 'dummy_application'
    result = cli_runner.invoke(microbial_order, [order_id, 'sign', '-a', application_tag],
                               obj=base_context)

    # THEN then it should complain on invalid order
    assert result.exit_code != SUCCESS


def test_invalid_order_non_empty_db(cli_runner, base_context, base_store: Store):
    # GIVEN a non empty database
    add_microbial_order(base_store)

    # WHEN running set with an order that does not exist
    order_id = 'dummy_order_id'
    application_tag = 'dummy_application'
    result = cli_runner.invoke(microbial_order, [order_id, 'sign', '-a', application_tag],
                               obj=base_context)

    # THEN then it should complain on invalid order
    assert result.exit_code != SUCCESS


def test_valid_order_no_apptag_option(cli_runner, base_context, base_store: Store):
    # GIVEN a non empty database
    order = add_microbial_order(base_store)

    # WHEN running set with an order that does not exist
    order_id = order.internal_id
    result = cli_runner.invoke(microbial_order, [order_id, 'sign'], obj=base_context)

    # THEN then it should just exit
    assert result.exit_code != SUCCESS


@pytest.mark.parametrize('option_key', [
    '--name',
    '--ticket',
])
def test_set_option(cli_runner, base_context, base_store: Store, option_key):

    # GIVEN a database with an order
    order = add_microbial_order(base_store)
    option_value = 'option_value'

    # WHEN calling set_microbial_order with option
    signature = 'sign'
    result = cli_runner.invoke(microbial_order, [order.internal_id, signature, option_key,
                                                 option_value], obj=base_context)

    # THEN then the option should have been set on the object and the user been informed
    assert result.exit_code == SUCCESS
    assert order.internal_id in result.output
    assert option_value in result.output
    assert option_value in base_store.MicrobialOrder.query.first().to_dict().values()
    assert signature in base_store.MicrobialOrder.query.first().comment


def test_set_project_name_in_lims(cli_runner, base_context, base_store):

    # GIVEN a database with an order
    order = add_microbial_order(base_store)
    name = 'a_name'

    # WHEN calling set_microbial_order with option
    signature = 'sign'
    result = cli_runner.invoke(microbial_order, [order.internal_id, signature, '--name',
                                                 name], obj=base_context)

    # THEN then the option should have been set on the object and the user been informed
    assert result.exit_code == SUCCESS
    assert 'LIMS' in result.output
    assert name in result.output
    assert name in base_context['lims'].get_updated_project_name()


@pytest.mark.parametrize('option_key', [
    '--name',
    '--ticket',
])
def test_set_option_with_same_value(cli_runner, base_context, base_store: Store, option_key):

    # GIVEN a database with an order
    order = add_microbial_order(base_store)
    option_value = 'option_value'
    first_sign = 'first_sign'
    second_sign = 'second_sign'

    # WHEN calling set_microbial_order with same option_value
    cli_runner.invoke(microbial_order, [order.internal_id, first_sign, option_key,
                                        option_value], obj=base_context)
    result = cli_runner.invoke(microbial_order, [order.internal_id, second_sign, option_key,
                                                 option_value], obj=base_context)

    # THEN then the second call should not render a change in comment
    assert result.exit_code == SUCCESS
    assert order.internal_id in result.output
    assert option_value in result.output
    assert option_value in base_store.MicrobialOrder.query.first().to_dict().values()
    assert first_sign in base_store.MicrobialOrder.query.first().comment
    assert second_sign not in base_store.MicrobialOrder.query.first().comment


def test_old_comment_preserved(cli_runner, base_context, base_store: Store):

    # GIVEN a database with an order
    order = add_microbial_order(base_store)
    first_sign = 'first_sign'
    second_sign = 'second_sign'

    # WHEN calling set_microbial_order twice with different signatures
    cli_runner.invoke(microbial_order, [order.internal_id, first_sign, '--name',
                                        'dummy_name1'], obj=base_context)
    result = cli_runner.invoke(microbial_order, [order.internal_id, second_sign, '--name',
                                                 'dummy_name2'], obj=base_context)

    # THEN both signatures should be found in the comment
    assert result.exit_code == SUCCESS
    assert first_sign in base_store.MicrobialOrder.query.first().comment
    assert second_sign in base_store.MicrobialOrder.query.first().comment


def ensure_application_version(store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(tag=application_tag, category='wgs',
                                            description='dummy_description', percent_kth=80)
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
