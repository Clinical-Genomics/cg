"""Tests the status part of the cg.store.api"""
from datetime import datetime


def test_samples_to_receive_external(sample_store):
    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding external samples to receive
    external_query = sample_store.samples_to_recieve(external=True)
    assert external_query.count() == 1
    first_sample = external_query.first()
    assert first_sample.application_version.application.is_external is True
    assert first_sample.received_at is None


def test_samples_to_receive_internal(sample_store):
    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding which samples are in queue to receive
    assert sample_store.samples_to_recieve().count() == 1
    first_sample = sample_store.samples_to_recieve().first()
    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None


def test_samples_to_sequence(sample_store):
    # GIVEN a store with sample in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.sequenced_at]) >= 1

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples = sample_store.samples_to_sequence()

    # THEN it should list the received and partly sequenced samples
    assert sequence_samples.count() == 2
    assert {sample.name for sample in sequence_samples} == set(
        ['sequenced-partly', 'received-prepared'])
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == 'sequenced-partly':
            assert sample.reads > 0


def test_case_in_uploaded_observations(sample_store):
    # GIVEN a case with observations that has been uploaded to loqusdb
    analysis = add_analysis(store=sample_store)

    sample = add_sample(sample_store, uploaded_to_loqus=True)
    sample_store.relate_sample(analysis.family, sample, 'unknown')
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    uploaded_observations = sample_store.observations_uploaded()

    # THEN the case should be in the returned collection
    assert analysis.family in uploaded_observations


def test_case_not_in_uploaded_observations(sample_store):
    # GIVEN a case with observations that has not been uploaded to loqusdb
    analysis = add_analysis(store=sample_store)

    sample = add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, 'unknown')
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    uploaded_observations = sample_store.observations_uploaded()

    # THEN the case should not be in the returned collection
    assert analysis.family not in uploaded_observations


def test_case_in_observations_to_upload(sample_store):
    # GIVEN a case with completed analysis and samples w/o loqus_id
    analysis = add_analysis(store=sample_store)

    sample = add_sample(sample_store)
    sample_store.relate_sample(analysis.family, sample, 'unknown')
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is None

    # WHEN getting observations to upload
    observations_to_upload = sample_store.observations_to_upload()

    # THEN the case should be in the returned collection
    assert analysis.family in observations_to_upload


def test_case_not_in_observations_to_upload(sample_store):
    # GIVEN a case with completed analysis and samples w loqus_id
    analysis = add_analysis(store=sample_store)

    sample = add_sample(sample_store, uploaded_to_loqus=True)
    sample_store.relate_sample(analysis.family, sample, 'unknown')
    assert analysis.family.analyses
    for link in analysis.family.links:
        assert link.sample.loqusdb_id is not None

    # WHEN getting observations to upload
    observations_to_upload = sample_store.observations_to_upload()

    # THEN the case should not be in the returned collection
    assert analysis.family not in observations_to_upload


def ensure_customer(store, customer_id='cust_test'):
    """utility function to return existing or create customer for tests"""
    customer_group = store.customer_group('dummy_group')
    if not customer_group:
        customer_group = store.add_customer_group('dummy_group', 'dummy group')

        customer = store.add_customer(internal_id=customer_id, name="Test Customer",
                                      scout_access=False, customer_group=customer_group,
                                      invoice_address='dummy_address',
                                      invoice_reference='dummy_reference')
        store.add_commit(customer)
    customer = store.customer(customer_id)
    return customer


def ensure_panel(store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(store, customer_id)
    panel = store.panel(panel_id)
    if not panel:
        panel = store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                version=1.0,
                                date=datetime.now(), genes=1)
        store.add_commit(panel)
    return panel


def add_family(store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(store)
    customer = ensure_customer(store, customer_id)
    family = store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    store.add_commit(family)
    return family


def add_analysis(store, family=None, completed_at=None):
    """Utility function to add an analysis for tests"""

    if not family:
        family = add_family(store)

    analysis = store.add_analysis(pipeline='', version='')

    if completed_at:
        analysis.completed_at = completed_at

    analysis.family = family
    store.add_commit(analysis)
    return analysis


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


def add_sample(store, sample_name='sample_test', uploaded_to_loqus=None):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex='unknown')
    sample.application_version_id = application_version_id
    sample.customer = customer
    if uploaded_to_loqus:
        sample.loqusdb_id = uploaded_to_loqus
    store.add_commit(sample)
    return sample