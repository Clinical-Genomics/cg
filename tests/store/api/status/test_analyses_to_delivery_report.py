"""This file tests the analyses_to_delivery_report part of the status api"""
from datetime import datetime, timedelta

from cg.constants import Pipeline
from cg.store import Store
from cg.utils.date import get_date


def test_missing(analysis_store: Store, helpers):
    """Tests that analyses that are completed but lacks delivery report are returned"""

    # GIVEN an analysis that is delivered but has no delivery report
    pipeline = Pipeline.BALSAMIC
    timestamp = datetime.now()
    analysis = helpers.add_analysis(analysis_store, started_at=timestamp, uploaded_at=timestamp)
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp, data_analysis=pipeline)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")
    assert sample.delivered_at is not None
    assert analysis.delivery_report_created_at is None

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report(pipeline=pipeline).all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_outdated(analysis_store, helpers):
    """Tests that analyses that have a delivery report but is older than the delivery are
    returned"""

    # GIVEN an analysis that is delivered but has an outdated delivery report
    pipeline = Pipeline.BALSAMIC
    timestamp = datetime.now()
    delivery_timestamp = timestamp - timedelta(days=1)
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp,
        uploaded_at=timestamp,
        delivery_reported_at=delivery_timestamp,
        pipeline=pipeline,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")
    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report(pipeline=pipeline).all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_outdated_analysis(analysis_store, helpers):
    """Tests that analyses that are older then when Hasta became production (2017-09-26) are not included in the cases to generate a delivery report for"""

    # GIVEN an analysis that is older than Hasta
    timestamp_old_analysis = get_date("2017-09-26")
    pipeline = Pipeline.BALSAMIC

    # GIVEN a delivery report created at date which is older than the upload date to trigger delivery report generation
    timestamp = datetime.now()
    delivery_reported_at_timestamp = timestamp - timedelta(days=1)

    # GIVEN a store to add analysis to
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_old_analysis,
        uploaded_at=timestamp,
        delivery_reported_at=delivery_reported_at_timestamp,
        pipeline=pipeline,
    )

    # GIVEN samples which has been delivered
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp)

    # GIVEN a store sample family relation
    analysis_store.relate_sample(family=analysis.family, sample=sample, status="unknown")

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report(pipeline=pipeline).all()

    # THEN this analyses should not be returned
    assert len(analyses) == 0
