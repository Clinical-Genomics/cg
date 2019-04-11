"""Tests the class that performs calculations on samples"""
from datetime import timedelta, datetime

from cg.meta.report.sample_calculator import SampleCalculator


def test_calculate_processing_days_invalid_delivered(sample_store):
    """Test calculate processing time when delivered_at is invalid"""

    # GIVEN sample with delivered_at None
    sample = add_sample(sample_store)
    yesterday = datetime.now() - timedelta(days=1)
    sample.received_at = yesterday
    sample.delivered_at = None

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is None
    assert processing_days is None


def test_calculate_processing_days_invalid_received(sample_store):
    """Test calculate processing time when received_at is invalid"""

    # GIVEN sample with no received_at but with delivered_at
    sample = add_sample(sample_store)
    today = datetime.now()
    sample.received_at = None
    sample.delivered_at = today

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is None
    assert processing_days is None


def test_calculate_processing_days_valid_dates(sample_store):
    """Test calculate processing time when all dates are present"""

    # GIVEN sample with received_at and delivered_at
    sample = add_sample(sample_store)
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()
    sample.received_at = yesterday
    sample.delivered_at = today

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is 1
    assert processing_days == 1


def add_sample(store, sample_id='sample_test', gender='female'):
    """utility function to add a sample to use in tests"""
    customer = ensure_customer(store)
    application_version_id = ensure_application_version(store).id
    sample = store.add_sample(name=sample_id, sex=gender)
    sample.application_version_id = application_version_id
    sample.customer = customer
    store.add_commit(sample)
    return sample


def ensure_application_version(store, application_tag='dummy_tag'):
    """utility function to return existing or create application version for tests"""
    application = store.application(tag=application_tag)
    if not application:
        application = store.add_application(tag=application_tag, category='wgs',
                                            description='dummy_description')
        store.add_commit(application)

    prices = {'standard': 10, 'priority': 20, 'express': 30, 'research': 5}
    version = store.application_version(application, 1)
    if not version:
        version = store.add_version(application, 1, valid_from=datetime.now(),
                                    prices=prices)

        store.add_commit(version)
    return version


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
