"""Test methods for cg/cli/set/sample"""
from datetime import datetime

from cg.store import Store


def test_set_sample_invalid_sample(invoke_cli, disk_store: Store):
    # GIVEN an empty database

    # WHEN running set with a sample that does not exist

    sample_id = 'dummy_sample_id'
    result = invoke_cli(['--database', disk_store.uri, 'set', 'sample', sample_id])

    # THEN then it should complain on invalid sample
    assert result.exit_code == 1


def test_set_sample_sex(invoke_cli, disk_store: Store):
    # GIVEN a database with a female sample

    sample_id = add_sample(disk_store, sex='female').internal_id
    new_sex = 'male'
    assert disk_store.Sample.query.first().sex != new_sex

    # WHEN setting sex on sample to male
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '--sex', new_sex])

    # THEN then it should have 'male' as sex
    assert result.exit_code == 0
    assert disk_store.Sample.query.first().sex == new_sex


def test_set_sample_invalid_customer(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    customer_id = 'dummy_customer_id'
    assert disk_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with an invalid customer
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-c', customer_id])

    # THEN then it should complain about missing customer instead of setting the value
    assert result.exit_code == 1


def test_set_sample_customer(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample and two customers
    sample_id = add_sample(disk_store).internal_id
    customer_id = ensure_customer(disk_store, 'another_customer').internal_id
    assert disk_store.Sample.query.first().customer.internal_id != customer_id

    # WHEN calling set sample with a valid customer
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-c', customer_id])

    # THEN then it should set the customer of the sample
    assert result.exit_code == 0
    assert disk_store.Sample.query.first().customer.internal_id == customer_id


def test_set_sample_comment(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample without a comment
    sample_id = add_sample(disk_store).internal_id
    comment = 'comment'
    assert comment not in (disk_store.Sample.query.first().comment or [])

    # WHEN calling set sample with a valid comment
    result = invoke_cli(['--database', disk_store.uri, 'set', 'sample', sample_id, '-C', comment])

    # THEN then it should add the comment to the sample
    assert result.exit_code == 0
    assert comment in disk_store.Sample.query.first().comment


def test_set_sample_second_comment(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample that has a comment
    sample_id = add_sample(disk_store).internal_id
    comment = 'comment'
    second_comment = 'comment2'
    invoke_cli(['--database', disk_store.uri, 'set', 'sample', sample_id, '-C', comment])
    assert comment in disk_store.Sample.query.first().comment
    assert second_comment not in disk_store.Sample.query.first().comment

    # WHEN calling set sample with second comment
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-C', second_comment])

    # THEN then it should add the second comment to the samples comments
    assert result.exit_code == 0
    assert comment in disk_store.Sample.query.first().comment
    assert second_comment in disk_store.Sample.query.first().comment


def test_set_sample_invalid_downsampled_to(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    downsampled_to = 'downsampled_to'
    assert disk_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with an invalid value of downsampled to
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-d', downsampled_to])

    # THEN then the value should have not been set on the sample
    assert result.exit_code == 2
    assert disk_store.Sample.query.first().downsampled_to != downsampled_to


def test_set_sample_downsampled_to(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    downsampled_to = 111111
    assert disk_store.Sample.query.first().downsampled_to != downsampled_to

    # WHEN calling set sample with a valid value of downsampled to
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-d', downsampled_to])

    # THEN then the value should have been set on the sample
    assert result.exit_code == 0
    assert disk_store.Sample.query.first().downsampled_to == downsampled_to


def test_set_sample_invalid_application(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    application_tag = 'dummy_application'
    assert disk_store.Sample.query.first().application_version.application.tag != application_tag

    # WHEN calling set sample with an invalid application
    result = invoke_cli(['--database', disk_store.uri, 'set', 'sample', sample_id, '-a',
                         application_tag])

    # THEN then it should complain about missing application instead of setting the value
    assert result.exit_code == 1
    assert disk_store.Sample.query.first().application_version.application.tag != application_tag


def test_set_sample_application(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample and two applications
    sample_id = add_sample(disk_store).internal_id
    application_tag = ensure_application_version(disk_store, 'another_application').application.tag
    assert disk_store.Sample.query.first().application_version.application.tag != application_tag

    # WHEN calling set sample with an invalid application
    result = invoke_cli(['--database', disk_store.uri, 'set', 'sample', sample_id, '-a',
                         application_tag])

    # THEN then the application should have been set
    assert result.exit_code == 0
    assert disk_store.Sample.query.first().application_version.application.tag == application_tag


def test_set_sample_capture_kit(invoke_cli, disk_store: Store):
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    capture_kit = 'capture_kit'
    assert disk_store.Sample.query.first().capture_kit != capture_kit

    # WHEN calling set sample with a valid capture_kit
    result = invoke_cli(
        ['--database', disk_store.uri, 'set', 'sample', sample_id, '-k', capture_kit])

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.Sample.query.first().capture_kit == capture_kit


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


def add_sample(disk_store, sample_id='sample_test', sex='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store).id
    sample = disk_store.add_sample(name=sample_id, sex=sex)
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample
