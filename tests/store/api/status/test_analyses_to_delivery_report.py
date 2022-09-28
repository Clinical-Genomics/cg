"""This file tests the analyses_to_delivery_report part of the status api"""
from datetime import datetime, timedelta

from cg.constants import Pipeline, DataDelivery
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.utils.date import get_date


def test_missing(analysis_store: Store, helpers, timestamp_now):
    """Tests that analyses that are completed, but lacks delivery report are returned."""

    # GIVEN an analysis that is delivered but has no delivery report
    pipeline = Pipeline.BALSAMIC
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_now,
        completed_at=timestamp_now,
        uploaded_at=timestamp_now,
        pipeline=pipeline,
        data_delivery=DataDelivery.SCOUT,
    )
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)
    analysis_store.relate_sample(
        family=analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
    )
    assert sample.delivered_at is not None
    assert analysis.delivery_report_created_at is None

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report(pipeline=pipeline).all()

    # THEN this analyse should be returned
    assert analysis in analyses


def test_outdated_analysis(analysis_store, helpers, timestamp_now, timestamp_yesterday):
    """Tests that analyses that are older then when Hasta became production (2017-09-26) are not included in the cases to generate a delivery report for"""

    # GIVEN an analysis that is older than Hasta
    timestamp_old_analysis = get_date("2017-09-26")
    pipeline = Pipeline.BALSAMIC

    # GIVEN a delivery report created at date which is older than the upload date to trigger delivery report generation

    # GIVEN a store to add analysis to
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_old_analysis,
        uploaded_at=timestamp_now,
        delivery_reported_at=timestamp_yesterday,
        pipeline=pipeline,
    )

    # GIVEN samples which has been delivered
    sample = helpers.add_sample(analysis_store, delivered_at=timestamp_now)

    # GIVEN a store sample case relation
    analysis_store.relate_sample(
        family=analysis.family, sample=sample, status=PhenotypeStatus.UNKNOWN
    )

    # WHEN calling the analyses_to_delivery_report
    analyses = analysis_store.analyses_to_delivery_report(pipeline=pipeline).all()

    # THEN this analyses should not be returned
    assert len(analyses) == 0


def test_analyses_to_upload_delivery_reports(analysis_store, helpers, timestamp_now):
    """Tests extraction of analyses ready for delivery report upload"""

    # GIVEN an analysis that has a delivery report generated
    pipeline = Pipeline.BALSAMIC
    analysis = helpers.add_analysis(
        analysis_store,
        started_at=timestamp_now,
        completed_at=timestamp_now,
        uploaded_at=None,
        delivery_reported_at=timestamp_now,
        pipeline=pipeline,
        data_delivery=DataDelivery.FASTQ_ANALYSIS_SCOUT,
    )

    # WHEN calling the analyses_to_upload_delivery_reports
    analyses = analysis_store.analyses_to_upload_delivery_reports(pipeline=pipeline).all()

    # THEN the previously defined analysis should be returned
    assert analysis in analyses
