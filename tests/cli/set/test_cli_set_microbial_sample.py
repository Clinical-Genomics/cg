"""Test methods for cg/cli/set/microbial_sample"""
from datetime import datetime

from cg.cli.set import microbial_sample
from cg.store import Store


SUCCESS = 0


def test_invalid_sample_empty_db(cli_runner, base_context):
    # GIVEN an empty database

    # WHEN running set with an sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_invalid_sample_non_empty_db(cli_runner, base_context, base_store: Store):
    # GIVEN a non empty database
    add_microbial_sample_and_order(base_store)

    # WHEN running set with an sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_valid_sample_no_apptag_option(cli_runner, base_context, base_store: Store):
    # GIVEN a non empty database
    sample = add_microbial_sample_and_order(base_store)

    # WHEN running set with an sample but without any options
    sample_id = sample.internal_id
    result = cli_runner.invoke(microbial_sample, [sample_id, "sign"], obj=base_context)

    # THEN then it should complain on missing options
    assert result.exit_code != SUCCESS


def test_invalid_application(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample = add_microbial_sample_and_order(base_store)
    application_tag = "dummy_application"
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-a", application_tag], obj=base_context
    )

    # THEN then it should complain about missing application instead of setting the value
    assert result.exit_code != SUCCESS
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )


def test_valid_application(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample and two applications
    sample = add_microbial_sample_and_order(base_store)
    application_tag = ensure_application_version(base_store, "another_application").application.tag
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an valid application
    signature = "sign"
    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-a", application_tag], obj=base_context
    )

    # THEN then the application should have been set
    assert result.exit_code == SUCCESS
    assert (
        base_store.MicrobialSample.query.first().application_version.application.tag
        == application_tag
    )
    assert signature in base_store.MicrobialSample.query.first().comment


def test_invalid_priority(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample = add_microbial_sample_and_order(base_store)
    priority = "dummy_priority"
    assert base_store.MicrobialSample.query.first().priority != priority

    # WHEN calling set sample with an invalid priority
    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-p", priority], obj=base_context
    )

    # THEN then it should complain about bad priority instead of setting the value
    assert result.exit_code != SUCCESS
    assert base_store.MicrobialSample.query.first().priority_human != priority


def test_valid_priority(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample = add_microbial_sample_and_order(base_store)
    priority = "priority"
    assert base_store.MicrobialSample.query.first().priority != priority

    # WHEN calling set sample with an valid priority
    signature = "sign"

    result = cli_runner.invoke(
        microbial_sample, [sample.internal_id, "sign", "-p", priority], obj=base_context
    )

    # THEN then the priority should have been set
    assert result.exit_code == SUCCESS
    assert base_store.MicrobialSample.query.first().priority_human == priority
    assert signature in base_store.MicrobialSample.query.first().comment


def ensure_application_version(store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(
            tag=application_tag, category="wgs", description="dummy_description", percent_kth=80
        )
        store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = store.application_version(application, 1)
    if not version:
        version = store.add_version(application, 1, valid_from=datetime.now(), prices=prices)
        store.add_commit(version)
    return version


def ensure_customer(store, customer_id="cust_test"):
    """utility function to return existing or create customer for tests"""
    customer_group_id = customer_id + "_group"
    customer_group = store.customer_group(customer_group_id)
    if not customer_group:
        customer_group = store.add_customer_group(customer_group_id, customer_group_id)

        customer = store.add_customer(
            internal_id=customer_id,
            name="Test Customer",
            scout_access=False,
            customer_group=customer_group,
            invoice_address="dummy_address",
            invoice_reference="dummy_reference",
        )
        store.add_commit(customer)
    customer = store.customer(customer_id)
    return customer


def add_organism(store):
    """utility function to add an organism to use in tests"""
    organism = store.add_organism(internal_id="organism_id", name="organism_name")
    return organism


def add_microbial_sample(store, sample_id="sample_test"):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version = ensure_application_version(store)
    organism = add_organism(store)
    sample = store.add_microbial_sample(
        name=sample_id,
        organism=organism,
        internal_id=sample_id,
        reference_genome="test",
        application_version=application_version,
    )
    sample.customer = customer
    return sample


def add_microbial_sample_and_order(store, order_id="sample_test", customer_id="cust_test"):
    """utility function to set a family to use in tests"""
    customer = ensure_customer(store, customer_id)
    with store.session.no_autoflush:
        order = store.add_microbial_order(name=order_id, customer=customer, ordered=datetime.now())
        order.customer = customer
        sample = add_microbial_sample(store)
        order.microbial_samples.append(sample)
    store.add_commit(sample)
    return sample
