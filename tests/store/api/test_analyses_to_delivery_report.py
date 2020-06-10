"""This file tests the analyses_to_delivery_report part of the status api"""
from datetime import datetime, timedelta

from cg.store import Store


def test_missing(analysis_store: Store, helpers):
    """Tests that analyses that are completed but lacks delivery report are returned"""

    # GIVEN an analysis that is delivered but has no delivery report
    timestamp = datetime.now()
    analysis = helpers.add_analysis(analysis_store, started_at=timestamp, uploaded_at=timestamp)
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")
    assert sample.delivered_at is not None
    assert analysis.delivery_report_created_at is None

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report().all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_outdated(analysis_store, helpers):
    """Tests that analyses that have a delivery report but is older than the delivery are
    returned"""

    # GIVEN an analysis that is delivered but has an outdated delivery report
    timestamp = datetime.now()
    delivery_timestamp = timestamp - timedelta(days=1)
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp,
        uploaded_at=timestamp,
        delivery_reported_at=delivery_timestamp,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")
    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report().all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_multiple_analyses(analysis_store, helpers):
    """Tests that analyses that are not latest are not returned"""

    # GIVEN an analysis that is not delivery reported but there exists a newer analysis
    timestamp = datetime.now()
    family = helpers.add_family(analysis_store)
    analysis_oldest = helpers.add_analysis(
        analysis_store,
        family=family,
        started_at=timestamp - timedelta(days=1),
        uploaded_at=timestamp - timedelta(days=1),
        delivery_reported_at=None,
    )
    analysis_store.add_commit(analysis_oldest)
    analysis_newest = helpers.add_analysis(
        analysis_store,
        family=family,
        started_at=timestamp,
        uploaded_at=timestamp,
        delivery_reported_at=None,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis_oldest.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report().all()

    # THEN only the newest analysis should be returned
    assert analysis_newest in analyses
    assert analysis_oldest not in analyses
