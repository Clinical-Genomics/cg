from datetime import datetime

from cg.store import Store
from cg.meta.analysis import AnalysisAPI


def test_store_completed_at_to_existing_analysis(analysis_store: Store, analysis_api: AnalysisAPI):
    """Store analysis should set completed_at on the analysis object"""

    # GIVEN a status db with a family with a started analysis
    analysis = add_analysis(analysis_store, started=True, completed=True, family_id='family')
    sample = add_sample(analysis_store)
    analysis_store.relate_sample(analysis.family, sample=sample, status='unknown')
    assert analysis.started_at
    assert analysis.completed_at
    nr_analyses_before_store_analysis = len(analysis.family.analyses)

    # WHEN storing the complete analysis
    config_stream = 'dummy_stream'
    analysis_api.store_analysis(config_stream)

    # THEN we should have an analysis object that is marked as completed
    assert nr_analyses_before_store_analysis == len(analysis.family.analyses) + 1
    assert analysis is analysis.family.analyses[0]
    assert analysis.started_at
    assert analysis.completed_at


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


def ensure_panel(disk_store, panel_id='panel_test', customer_id='cust_test'):
    """utility function to add a panel to use in tests"""
    customer = ensure_customer(disk_store, customer_id)
    panel = disk_store.panel(panel_id)
    if not panel:
        panel = disk_store.add_panel(customer=customer, name=panel_id, abbrev=panel_id,
                                     version=1.0,
                                     date=datetime.now(), genes=1)
        disk_store.add_commit(panel)
    return panel


def add_family(disk_store, family_id='family_test', customer_id='cust_test',
               action=None, priority=None):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.internal_id = family_id
    family.customer = customer
    family.ordered_at = datetime.now()
    if action:
        family.action = action
    if priority:
        family.priority = priority
    disk_store.add_commit(family)
    return family


def add_analysis(store, started=False, pipeline=None, family_id='family_test'):
    """Utility function to add an analysis for tests"""
    family = add_family(store, family_id)
    analysis = store.add_analysis(pipeline='', version='')
    if started:
        analysis.started_at = datetime.now()
    if pipeline:
        analysis.pipeline = pipeline

    family.analyses.append(analysis)
    store.add_commit(analysis)
    return analysis


def add_sample(store, sample_name='sample_test', received=False, prepared=False,
               sequenced=False, delivered=False, invoiced=False, data_analysis=None,
               is_external=False, no_invoice=False, date=datetime.now()):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex='unknown')
    sample.application_version_id = application_version_id
    sample.customer = customer
    if received:
        sample.received_at = date
    if prepared:
        sample.prepared_at = date
    if sequenced:
        sample.sequenced_at = date
    if delivered:
        sample.delivered_at = date
    if invoiced:
        invoice = store.add_invoice(customer)
        sample.invoice = invoice
        sample.invoice.invoiced_at = date
    if data_analysis:
        sample.data_analysis = data_analysis
    if is_external:
        sample.is_external = is_external
    if no_invoice:
        sample.no_invoice = no_invoice
    store.add_commit(sample)
    return sample
