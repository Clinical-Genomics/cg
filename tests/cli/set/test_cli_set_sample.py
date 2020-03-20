"""Test methods for cg/cli/set/sample"""
from datetime import datetime

from cg.cli.set import sample
from cg.store import Store

SUCCESS = 0


def test_set_sample_invalid_sample(cli_runner, base_context):
    # GIVEN an empty database

    # WHEN running set with a sample that does not exist
    sample_id = "dummy_sample_id"
    result = cli_runner.invoke(sample, [sample_id], obj=base_context)

    # THEN then it should complain on invalid sample
    assert result.exit_code != SUCCESS


def test_set_sample_name(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a female sample

    sample_id = add_sample(base_store, sex="female").internal_id
    new_name = "urban"
    assert base_store.Sample.query.first().name != new_name

    # WHEN setting sex on sample to 'urban'
    result = cli_runner.invoke(
        sample, [sample_id, "--name", new_name], obj=base_context
    )

    # THEN then it should have 'urban' as name
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().name == new_name
    assert base_context["lims"].get_updated_sample_name() == new_name


def test_set_sample_sex(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a female sample

    sample_id = add_sample(base_store, sex="female").internal_id
    new_sex = "male"
    assert base_store.Sample.query.first().sex != new_sex

    # WHEN setting sex on sample to male
    result = cli_runner.invoke(sample, [sample_id, "--sex", new_sex], obj=base_context)

    # THEN then it should have 'male' as sex
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().sex == new_sex
    assert base_context["lims"].get_updated_sample_sex() == new_sex


def test_set_sample_invalid_customer(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(base_store).internal_id
    customer_id = "dummy_customer_id"
    assert base_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with an invalid customer
    result = cli_runner.invoke(sample, [sample_id, "-c", customer_id], obj=base_context)

    # THEN then it should warn about missing customer instead of setting the value
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().customer.internal_id != customer_id


def test_set_sample_customer(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample and two customers
    sample_id = add_sample(base_store).internal_id
    customer_id = ensure_customer(base_store, "another_customer").internal_id
    assert base_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with a valid customer
    result = cli_runner.invoke(sample, [sample_id, "-c", customer_id], obj=base_context)

    # THEN then it should set the customer of the sample
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().customer.internal_id == customer_id


def test_set_sample_comment(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample without a comment
    sample_id = add_sample(base_store).internal_id
    comment = "comment"
    assert comment not in (base_store.Sample.query.first().comment or [])

    # WHEN calling set sample with a valid comment
    result = cli_runner.invoke(sample, [sample_id, "-C", comment], obj=base_context)

    # THEN then it should add the comment to the sample
    assert result.exit_code == SUCCESS
    assert comment in base_store.Sample.query.first().comment


def test_set_sample_second_comment(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample that has a comment
    sample_id = add_sample(base_store).internal_id
    comment = "comment"
    second_comment = "comment2"
    cli_runner.invoke(sample, [sample_id, "-C", comment], obj=base_context)

    assert comment in base_store.Sample.query.first().comment
    assert second_comment not in base_store.Sample.query.first().comment

    # WHEN calling set sample with second comment
    result = cli_runner.invoke(
        sample, [sample_id, "-C", second_comment], obj=base_context
    )

    # THEN then it should add the second comment to the samples comments
    assert result.exit_code == SUCCESS
    assert comment in base_store.Sample.query.first().comment
    assert second_comment in base_store.Sample.query.first().comment


def test_set_sample_invalid_downsampled_to(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    downsampled_to = "downsampled_to"

    # WHEN calling set sample with an invalid value of downsampled to
    result = cli_runner.invoke(
        sample, ["dummy_sample_id", "-d", downsampled_to], obj=base_context
    )

    # THEN wrong data type
    assert result.exit_code != SUCCESS


def test_set_sample_downsampled_to(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(base_store).internal_id
    downsampled_to = 111111
    assert base_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-d", downsampled_to], obj=base_context
    )

    # THEN then the value should have been set on the sample
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().downsampled_to == downsampled_to


def test_set_sample_reset_downsampled_to(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(base_store).internal_id
    downsampled_to = 0
    assert base_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid reset value of downsampled to
    result = cli_runner.invoke(
        sample, [sample_id, "-d", downsampled_to], obj=base_context
    )

    # THEN then the value should have been set on the sample
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().downsampled_to is None


def test_set_sample_invalid_application(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(base_store).internal_id
    application_tag = "dummy_application"
    assert (
        base_store.Sample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        sample, [sample_id, "-a", application_tag], obj=base_context
    )

    # THEN then it should warn about missing application instead of setting the value
    assert result.exit_code == SUCCESS
    assert (
        base_store.Sample.query.first().application_version.application.tag
        != application_tag
    )


def test_set_sample_application(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample and two applications
    sample_id = add_sample(base_store).internal_id
    application_tag = ensure_application_version(
        base_store, "another_application"
    ).application.tag
    assert (
        base_store.Sample.query.first().application_version.application.tag
        != application_tag
    )

    # WHEN calling set sample with an invalid application
    result = cli_runner.invoke(
        sample, [sample_id, "-a", application_tag], obj=base_context
    )

    # THEN then the application should have been set
    assert result.exit_code == SUCCESS
    assert (
        base_store.Sample.query.first().application_version.application.tag
        == application_tag
    )


def test_set_sample_capture_kit(cli_runner, base_context, base_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(base_store).internal_id
    capture_kit = "capture_kit"
    assert base_store.Sample.query.first().capture_kit != capture_kit

    # WHEN calling set sample with a valid capture_kit
    result = cli_runner.invoke(sample, [sample_id, "-k", capture_kit], obj=base_context)

    # THEN then it should be added
    assert result.exit_code == SUCCESS
    assert base_store.Sample.query.first().capture_kit == capture_kit


def ensure_application_version(store, application_tag="dummy_tag"):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(
            tag=application_tag,
            category="wgs",
            description="dummy_description",
            percent_kth=80,
        )
        store.add_commit(application)

    prices = {"standard": 10, "priority": 20, "express": 30, "research": 5}
    version = store.application_version(application, 1)
    if not version:
        version = store.add_version(
            application, 1, valid_from=datetime.now(), prices=prices
        )

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


def add_sample(store, sample_id="sample_test", sex="female"):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample_obj = store.add_sample(name=sample_id, sex=sex)
    sample_obj.application_version_id = application_version_id
    sample_obj.customer = customer
    store.add_commit(sample_obj)
    return sample_obj
