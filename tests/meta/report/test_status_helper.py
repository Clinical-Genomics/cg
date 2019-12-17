""" Test the status database report helper"""
from datetime import datetime, timedelta

from cg.meta.report.status_helper import StatusHelper


def test_get_previous_report_version_when_only_one(store):

    # GIVEN two analyses for the given family
    first_analysis = add_analysis(store)

    # WHEN fetching previous_report_version
    report_version = StatusHelper.get_previous_report_version(first_analysis)

    # THEN the version should be None
    assert not report_version


def test_get_previous_report_version_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    add_analysis(store, first_analysis.family, completed_at=yesterday)

    # WHEN fetching previous_report_version
    report_version = StatusHelper.get_previous_report_version(first_analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_first_analysis_when_only_one(store):

    # GIVEN one analysis for the given family
    analysis = add_analysis(store)
    assert len(analysis.family.analyses) == 1

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_first_analysis_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    second_analysis = add_analysis(store, first_analysis.family, completed_at=yesterday)

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(second_analysis)

    # THEN the version should be 1
    assert report_version == 1


def test_second_analysis_when_two(store):

    # GIVEN two analyses for the given family
    yesterday = datetime.now() - timedelta(days=1)
    first_analysis = add_analysis(store, completed_at=datetime.now())
    second_analysis = add_analysis(store, first_analysis.family, completed_at=yesterday)
    assert first_analysis.family.analyses.index(second_analysis) == 1
    assert first_analysis.family.analyses.index(first_analysis) == 0

    # WHEN fetching report_version
    report_version = StatusHelper.get_report_version(second_analysis)

    # THEN the version should be 1
    assert report_version == 1


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


def add_family(disk_store, family_id='family_test', customer_id='cust_test'):
    """utility function to add a family to use in tests"""
    panel = ensure_panel(disk_store)
    customer = ensure_customer(disk_store, customer_id)
    family = disk_store.add_family(name=family_id, panels=panel.name)
    family.customer = customer
    disk_store.add_commit(family)
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
