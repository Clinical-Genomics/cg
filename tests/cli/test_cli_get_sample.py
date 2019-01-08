"""This script tests the cli methods to get samples in status-db"""
from datetime import datetime

from cg.store import Store


def test_get_sample_bad_sample(invoke_cli, disk_store: Store):
    """Test to get a sample using a non-existing sample-id """
    # GIVEN an empty database

    # WHEN getting a sample
    db_uri = disk_store.uri
    name = 'dummy_name'
    result = invoke_cli(['--database', db_uri, 'get', 'sample', name])

    # THEN then it should warn about missing sample id instead of getting a sample
    # it will not fail since the API accepts multiple samples
    assert result.exit_code == 0


def test_get_sample_required(invoke_cli, disk_store: Store):
    """Test to get a sample using only the required argument"""
    # GIVEN a database with a sample
    sample_id = add_sample(disk_store).internal_id
    assert disk_store.Sample.query.count() == 1

    # WHEN getting a sample
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert sample_id in result.output


def test_get_samples_required(invoke_cli, disk_store: Store):
    """Test to get several samples using only the required arguments"""
    # GIVEN a database with two samples
    sample_id1 = add_sample(disk_store, '1').internal_id
    sample_id2 = add_sample(disk_store, '2').internal_id
    assert disk_store.Sample.query.count() == 2

    # WHEN getting a sample
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id1, sample_id2])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert sample_id1 in result.output
    assert sample_id2 in result.output


def test_get_sample_output(invoke_cli, disk_store: Store):
    """Test that the output has the data of the sample"""
    # GIVEN a database with a sample with data
    sample = add_sample(disk_store)
    sample_id = sample.internal_id
    name = sample.name
    customer_id = sample.customer.internal_id
    application_tag = sample.application_version.application.tag
    state = sample.state
    priority_human = sample.priority_human

    # WHEN getting a sample
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert sample_id in result.output
    assert name in result.output
    assert customer_id in result.output
    assert application_tag in result.output
    assert state in result.output
    assert priority_human in result.output


def test_get_sample_external_false(invoke_cli, disk_store: Store):
    """Test that the output has the external-value of the sample"""
    # GIVEN a database with a sample with data
    sample_id = add_sample(disk_store, is_external=False).internal_id
    is_external_false = 'No'
    is_external_true = 'Yes'

    # WHEN getting a sample
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert is_external_false in result.output
    assert is_external_true not in result.output


def test_get_sample_external_true(invoke_cli, disk_store: Store):
    """Test that the output has the external-value of the sample"""
    # GIVEN a database with a sample with data
    sample_id = add_sample(disk_store, is_external=True).internal_id
    is_external_false = 'No'
    is_external_true = 'Yes'

    # WHEN getting a sample
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id])

    # THEN then it should have been get
    assert result.exit_code == 0
    assert is_external_true in result.output
    assert is_external_false not in result.output


def test_get_sample_no_families_without_family(invoke_cli, disk_store: Store):
    """Test that the --no-families flag works without families"""
    # GIVEN a database with a sample without related samples
    name = add_sample(disk_store).internal_id
    assert not disk_store.Sample.query.first().links

    # WHEN getting a sample with the --no-families flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', name, '--no-families'])

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_no_families_with_family(invoke_cli, disk_store: Store):
    """Test that the --no-families flag doesn't show family info"""
    # GIVEN a database with a sample with related samples
    family = add_family(disk_store)
    sample = add_sample(disk_store)
    link = add_relationship(disk_store, sample=sample, family=family)
    assert link in disk_store.Sample.query.first().links
    sample_id = sample.internal_id

    # WHEN getting a sample with the --no-families flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id, '--no-families'])

    # THEN all related families should be listed in the output
    assert result.exit_code == 0
    for link in disk_store.Sample.query.first().links:
        assert link.family.internal_id not in result.output


def test_get_sample_families_without_family(invoke_cli, disk_store: Store):
    """Test that the --families flag works without families"""
    # GIVEN a database with a sample without related samples
    sample_id = add_sample(disk_store).internal_id
    assert not disk_store.Sample.query.first().links

    # WHEN getting a sample with the --families flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id, '--families'])

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_families_with_family(invoke_cli, disk_store: Store):
    """Test that the --families flag does show family info"""
    # GIVEN a database with a sample with related samples
    family = add_family(disk_store)
    sample = add_sample(disk_store)
    sample_id = sample.internal_id
    add_relationship(disk_store, sample, family)
    assert disk_store.Sample.query.first().links

    # WHEN getting a sample with the --families flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id, '--families'])

    # THEN all related families should be listed in the output
    assert result.exit_code == 0
    for link in disk_store.Sample.query.first().links:
        assert link.family.internal_id in result.output


def test_get_sample_flowcells_without_flowcell(invoke_cli, disk_store: Store):
    """Test that we can query samples for flowcells even when there are none"""
    # GIVEN a database with a sample without related flowcells
    sample_id = add_sample(disk_store).internal_id
    assert not disk_store.Flowcell.query.first()

    # WHEN getting a sample with the --flowcells flag
    db_uri = disk_store.uri
    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id, '--flowcells'])

    # THEN everything is fine
    assert result.exit_code == 0


def test_get_sample_flowcells_with_flowcell(invoke_cli, disk_store: Store):
    """Test that we can query samples for flowcells and that the flowcell name is in the output"""
    # GIVEN a database with a sample and a related flowcell
    flowcell = add_flowcell(disk_store)
    sample = add_sample(disk_store, flowcell=flowcell)
    assert flowcell in disk_store.Sample.query.first().flowcells
    sample_id = sample.internal_id

    # WHEN getting a sample with the --flowcells flag
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'get', 'sample', sample_id, '--flowcells'])

    # THEN the related flowcell should be listed in the output
    assert result.exit_code == 0
    for flowcell in disk_store.Sample.query.first().flowcells:
        assert flowcell.name in result.output


def ensure_application_version(disk_store, application_tag='dummy_tag', is_external=False):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 description='dummy_description',
                                                 is_external=is_external)
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


def add_sample(disk_store, sample_id='test_sample', is_external=False, flowcell=None):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store, is_external=is_external).id
    sample = disk_store.add_sample(name=sample_id, sex='female')
    sample.application_version_id = application_version_id
    sample.customer = customer
    sample.is_external = is_external
    if flowcell:
        sample.flowcells.append(flowcell)
    disk_store.add_commit(sample)
    return sample


def add_flowcell(disk_store, sample_id='flowcell_test', sample=None):
    """utility function to get a flowcell to use in tests"""
    flowcell = disk_store.add_flowcell(name=sample_id, sequencer='dummy_sequencer',
                                       sequencer_type='hiseqx',
                                       date=datetime.now())
    if sample:
        flowcell.samples.append(sample)
    disk_store.add_commit(flowcell)
    return flowcell


def add_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                 version=1.0,
                                 date=datetime.now(), genes=1)
    disk_store.add_commit(panel)
    return panel


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel_name = add_panel(disk_store).name
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel_name)
    family.customer = customer
    disk_store.add_commit(family)
    return family


def add_relationship(disk_store, sample, family):
    """utility function to add a sample to use in tests"""
    link = disk_store.relate_sample(sample=sample, family=family, status='unknown')
    disk_store.add_commit(link)
    return link
