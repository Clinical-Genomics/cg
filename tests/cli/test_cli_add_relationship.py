"""This script tests the cli methods to add families to status-db"""
from datetime import datetime

from cg.store import Store


def test_add_relationship_required(invoke_cli, disk_store: Store):
    """Test to add a relationship using only the required arguments"""
    # GIVEN a database with a sample and an family
    sample_id = add_sample(disk_store)
    family_id = add_family(disk_store)
    status = 'affected'

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship',
         family_id, sample_id, '-s', status])

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().family.internal_id == family_id
    assert disk_store.FamilySample.query.first().sample.internal_id == sample_id


def test_add_relationship_bad_sample(invoke_cli, disk_store: Store):
    """Test to add a relationship using a non-existing sample"""
    # GIVEN an empty database

    # WHEN adding a relationship
    db_uri = disk_store.uri
    family_id = add_family(disk_store)
    sample_id = 'dummy_sample'
    status = 'affected'
    result = invoke_cli(['--database', db_uri, 'add', 'relationship',
                         family_id, sample_id, '-s', status])

    # THEN then it should complain on missing sample instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_bad_family(invoke_cli, disk_store: Store):
    """Test to add a relationship using a non-existing family"""
    # GIVEN a database with a sample

    # WHEN adding a relationship
    db_uri = disk_store.uri
    family_id = 'dummy_family'
    sample_id = add_sample(disk_store)
    status = 'affected'
    result = invoke_cli(['--database', db_uri, 'add', 'relationship',
                         family_id, sample_id, '-s', status])

    # THEN then it should complain in missing family instead of adding a relationship
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_bad_status(invoke_cli, disk_store: Store):
    """Test that the added relationship get the status we send in"""
    # GIVEN a database with a sample and an family

    # WHEN adding a relationship
    db_uri = disk_store.uri

    sample_id = add_sample(disk_store)
    family_id = add_family(disk_store)
    status = 'dummy_status'

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship', family_id,
         sample_id, '-s', status])

    # THEN then it should complain on bad status instead of adding a relationship
    assert result.exit_code == 2
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_mother(invoke_cli, disk_store: Store):
    """Test to add a relationship with a mother"""
    # GIVEN a database with a sample and an family
    sample_id = add_sample(disk_store)
    mother_id = add_sample(disk_store, 'mother')
    family_id = add_family(disk_store)
    status = 'affected'

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship',
         family_id, sample_id, '-s', status, '-m', mother_id])

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().mother.internal_id == mother_id


def test_add_relationship_bad_mother(invoke_cli, disk_store: Store):
    """Test to add a relationship using a non-existing mother"""
    # GIVEN a database with a sample and an family
    sample_id = add_sample(disk_store)
    mother_id = 'dummy_mother'
    family_id = add_family(disk_store)
    status = 'affected'

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship',
         family_id, sample_id, '-s', status, '-m', mother_id])

    # THEN then it should not be added
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def test_add_relationship_father(invoke_cli, disk_store: Store):
    """Test to add a relationship using a father"""
    # GIVEN a database with a sample and an family
    sample_id = add_sample(disk_store)
    father_id = add_sample(disk_store, 'father', 'male')
    family_id = add_family(disk_store)
    status = 'affected'

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship',
         family_id, sample_id, '-s', status, '-f', father_id])

    # THEN then it should be added
    assert result.exit_code == 0
    assert disk_store.FamilySample.query.count() == 1
    assert disk_store.FamilySample.query.first().father.internal_id == father_id


def test_add_relationship_bad_father(invoke_cli, disk_store: Store):
    """Test to add a relationship using a non-existing father"""
    # GIVEN a database with a sample and an family
    sample_id = add_sample(disk_store)
    father_id = 'bad_father'
    family_id = add_family(disk_store)
    status = 'affected'

    # WHEN adding a relationship
    db_uri = disk_store.uri

    result = invoke_cli(
        ['--database', db_uri, 'add', 'relationship',
         family_id, sample_id, '-s', status, '-f', father_id])

    # THEN then it should not be added
    assert result.exit_code == 1
    assert disk_store.FamilySample.query.count() == 0


def ensure_application_version(disk_store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = disk_store.application(tag=application_tag)
    if not application:
        application = disk_store.add_application(tag=application_tag, category='wgs',
                                                 percent_kth=80, description='dummy_description')
        disk_store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = disk_store.application_version(application, 1)
    if not version:
        version = disk_store.add_version(application, 1, valid_from=datetime.now(),
                                         prices=prices)

        disk_store.add_commit(version)
    return version.id


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


def add_sample(disk_store, sample_id='sample_test', gender='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(disk_store)
    application_version_id = ensure_application_version(disk_store)
    sample = disk_store.add_sample(name=sample_id, sex=gender)
    sample.application_version_id = application_version_id
    sample.customer = customer
    disk_store.add_commit(sample)
    return sample.internal_id


def add_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                 version=1.0,
                                 date=datetime.now(), genes=1)
    disk_store.add_commit(panel)
    return panel_id


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel = add_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel)
    family.customer = customer
    disk_store.add_commit(family)
    return family.internal_id
