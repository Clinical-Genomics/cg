"""This file tests the analyses_to_delivery_report part of the status api"""
from datetime import datetime, timedelta

from cg.store import Store


def test_analyses_to_delivery_report_missing(analysis_store: Store):
    """Tests that analyses that are completed but lacks delivery report are returned"""

    # GIVEN an analysis that is delivered but has no delivery report
    analysis = add_analysis(analysis_store)
    sample = add_sample(analysis_store, delivered=True)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status='unknown')
    assert sample.delivered_at is not None
    assert analysis.delivery_report_created_at is None

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report().all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_analyses_to_delivery_report_outdated(analysis_store):
    """Tests that analyses that have a delivery report but is older than the delivery are
    returned"""

    # GIVEN an analysis that is delivered but has an outdated delivery report
    analysis = add_analysis(analysis_store, old_delivery_report=True)
    sample = add_sample(analysis_store, delivered=True)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status='unknown')
    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report().all()

    # THEN this analyse should be returned
    assert analysis in analyses


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


def add_sample(store, sample_name='sample_test', delivered=False, date=datetime.now()):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_name, sex='unknown')
    sample.application_version_id = application_version_id
    sample.customer = customer
    if delivered:
        sample.delivered_at = date
    store.add_commit(sample)
    return sample


def add_family(disk_store, family_id='family_test', customer_id='cust_test', ordered_days_ago=0,
               action=None, priority=None):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    family.ordered_at = datetime.now() - timedelta(days=ordered_days_ago)
    if action:
        family.action = action
    if priority:
        family.priority = priority
    disk_store.add_commit(family)
    return family


def add_analysis(store, completed=False, delivered=False, old_delivery_report=False):
    """Utility function to add an analysis for tests"""
    family = add_family(store)
    analysis = store.add_analysis(pipeline='', version='')
    if completed:
        analysis.completed_at = datetime.now()
    if delivered:
        analysis.delivered_at = datetime.now()
    if old_delivery_report:
        analysis.delivery_report_created_at = datetime.now() - timedelta(days=1)
        analysis.delivered_at = datetime.now()

    family.analyses.append(analysis)
    store.add_commit(analysis)
    return analysis
