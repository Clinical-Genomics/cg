"""Tests the findbusinessdata part of the Cg store API related to Analysis model."""
from datetime import datetime
from typing import List
from cg.store import Store
from cg.store.models import (
    Analysis,
)
from cg.constants import Pipeline


def test_get_latest_nipt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store,
    timestamp_now: datetime,
    pipeline: str = Pipeline.FLUFFY,
):
    """Test get the latest NIPT analysis to upload."""
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN fetching the latest analysis to upload to nipt
    analyses: List[
        Analysis
    ] = store_with_analyses_for_cases_not_uploaded_fluffy.get_latest_analysis_to_upload_for_pipeline(
        pipeline=pipeline
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.started_at == timestamp_now
        assert analysis.uploaded_at is None
        assert analysis.pipeline == pipeline


def test_get_latest_microsalt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_microsalt: Store,
    timestamp_now: datetime,
    pipeline: str = Pipeline.MICROSALT,
):
    """Test get the latest microsalt analysis to upload."""
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN fetching the latest analysis to upload to microsalt
    analyses: List[
        Analysis
    ] = store_with_analyses_for_cases_not_uploaded_microsalt.get_latest_analysis_to_upload_for_pipeline(
        pipeline=pipeline
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.started_at == timestamp_now
        assert analysis.uploaded_at is None
        assert analysis.pipeline == pipeline


def test_get_analyses_to_deliver_for_pipeline(
    store_with_analyses_for_cases_to_deliver: Store,
    pipeline: Pipeline = Pipeline.FLUFFY,
):
    # GIVEN a store with multiple analyses to deliver

    # WHEN fetching the latest analysis to upload to nipt
    analyses = store_with_analyses_for_cases_to_deliver.get_analyses_to_deliver_for_pipeline(
        pipeline=pipeline
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.family.internal_id in ["test_case_1", "yellowhog"]
        assert analysis.uploaded_at is None
        assert analysis.pipeline == pipeline


def test_get_analyses(store_with_analyses_for_cases: Store):
    """Test all analyses can be returned."""
    # GIVEN a database with an analysis and case

    # WHEN fetching all analyses
    analysis: List[Analysis] = store_with_analyses_for_cases.get_analyses()

    # THEN one analysis should be returned
    assert len(analysis) == store_with_analyses_for_cases._get_query(table=Analysis).count()
