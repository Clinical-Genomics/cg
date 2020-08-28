"""Tests the class that performs calculations on samples"""
from datetime import datetime, timedelta

from cg.meta.report.sample_calculator import SampleCalculator


def test_calculate_processing_days_invalid_delivered(sample_store, helpers):
    """Test calculate processing time when delivered_at is invalid"""

    # GIVEN sample with delivered_at None
    sample = helpers.add_sample(sample_store)
    yesterday = datetime.now() - timedelta(days=1)
    sample.received_at = yesterday
    sample.delivered_at = None

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is None
    assert processing_days is None


def test_calculate_processing_days_invalid_received(sample_store, helpers):
    """Test calculate processing time when received_at is invalid"""

    # GIVEN sample with no received_at but with delivered_at
    sample = helpers.add_sample(sample_store)
    today = datetime.now()
    sample.received_at = None
    sample.delivered_at = today

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is None
    assert processing_days is None


def test_calculate_processing_days_valid_dates(sample_store, helpers):
    """Test calculate processing time when all dates are present"""

    # GIVEN sample with received_at and delivered_at
    sample = helpers.add_sample(sample_store)
    yesterday = datetime.now() - timedelta(days=1)
    today = datetime.now()
    sample.received_at = yesterday
    sample.delivered_at = today

    # WHEN calculate_processing_days
    processing_days = SampleCalculator.calculate_processing_days(sample)

    # THEN calculated processing days is 1
    assert processing_days == 1
