"""This script tests the cli methods to get flowcells in status-db"""
from datetime import datetime

from cg.store import Store


def test_get_flowcell_bad_flowcell(invoke_cli, disk_store: Store):
    """Test to get a flowcell using a non-existing flowcell """
    # GIVEN an empty database

    # WHEN getting a flowcell
    db_uri = disk_store.uri
    name = 'dummy_name'
    result = invoke_cli(['--database', db_uri, 'get', 'flowcell', name])

    # THEN then it should complain in missing flowcell instead of getting a flowcell
    assert result.exit_code == 1


def test_get_flowcell_required(invoke_cli, disk_store: Store):
    """Test to get a flowcell using only the required arguments"""
    # GIVEN a database with a flowcell
    flowcell_name = add_flowcell(disk_store).name
    assert disk_store.Flowcell.query.count() == 1

    # WHEN getting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name])

    # THEN then it should have been get
    assert result.exit_code == 0


def test_get_flowcell_output(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell with data
    flowcell_name = add_flowcell(disk_store).name
    sequencer_type = disk_store.Flowcell.query.first().sequencer_type
    sequencer_name = disk_store.Flowcell.query.first().sequencer_name
    sequenced_at_date = str(disk_store.Flowcell.query.first().sequenced_at.date())
    status = disk_store.Flowcell.query.first().status

    # WHEN getting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert flowcell_name in result.output
    assert sequencer_type in result.output
    assert sequencer_name in result.output
    assert sequenced_at_date in result.output
    assert status in result.output


def test_get_flowcell_archived_at_none(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell with data
    flowcell_name = add_flowcell(disk_store, archived_at=None).name
    archived_at = 'No'

    # WHEN getting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert archived_at in result.output


def test_get_flowcell_archived_at_date(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell with data
    archived_at = datetime.now()
    flowcell_name = add_flowcell(disk_store, archived_at=archived_at).name
    archived_at_date = str(archived_at.date())

    # WHEN getting a flowcell
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert archived_at_date in result.output


def test_get_flowcell_samples_without_samples(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell without related samples
    flowcell_name = add_flowcell(disk_store).name
    assert not disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --samples flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name, '--samples'])

    # THEN a message about no samples should have been displayed
    assert result.exit_code == 0
    assert 'no samples found on flowcell' in result.output


def test_get_flowcell_samples(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell with related samples
    samples = add_samples(disk_store)
    flowcell_name = add_flowcell(disk_store, samples=samples).name
    assert disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --samples flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name, '--samples'])

    # THEN all related samples should be listed in the output
    assert result.exit_code == 0
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id in result.output


def test_get_flowcell_no_samples_without_samples(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell without related samples
    flowcell_name = add_flowcell(disk_store).name
    assert not disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --no-samples flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name, '--no-samples'])

    # THEN there are no samples to display but everything is OK
    assert result.exit_code == 0


def test_get_flowcell_no_samples_with_samples(invoke_cli, disk_store: Store):
    """Test that the output has the data of the flowcell"""
    # GIVEN a database with a flowcell with related samples
    samples = add_samples(disk_store)
    flowcell_name = add_flowcell(disk_store, samples=samples).name
    assert disk_store.Flowcell.query.first().samples

    # WHEN getting a flowcell with the --no-samples flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'flowcell', flowcell_name, '--no-samples'])

    # THEN no related samples should be listed in the output
    assert result.exit_code == 0
    for sample in disk_store.Flowcell.query.first().samples:
        assert sample.internal_id not in result.output


def add_flowcell(disk_store, name='flowcell_test', archived_at=None, samples=None):
    """utility function to get a flowcell to use in tests"""
    flowcell = disk_store.add_flowcell(name=name, sequencer='dummy_sequencer',
                                       sequencer_type='hiseqx',
                                       date=datetime.now())
    flowcell.archived_at = archived_at
    if samples:
        flowcell.samples = samples
    disk_store.add_commit(flowcell)
    return flowcell


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


def add_sample(disk_store, sample_id):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store).id
    sample = disk_store.add_sample(name=sample_id, sex='female')
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample


def add_samples(disk_store):
    """utility function to add a samples to use in tests"""
    samples = []
    for i in range(1, 5):
        samples.append(add_sample(disk_store, str(i)))
    return samples
