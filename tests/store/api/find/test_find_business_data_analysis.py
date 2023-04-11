"""Tests the findbusinessdata part of the Cg store API related to Analysis model."""
from datetime import datetime
from typing import List
from cg.store import Store
from cg.store.models import (
    Analysis,
)
from tests.store_helpers import StoreHelpers
from cg.constants import Pipeline


def test_get_analysis_by_case(
    store_with_case_and_analysis: Store, case_id: str = "test_case_internal_id"
):
    """Test that an analysis can be fetched by case."""
    # GIVEN a database with an analysis and case
    case = store_with_case_and_analysis.get_case_by_internal_id(internal_id=case_id)
    assert case
    # WHEN fetching the analysis by case
    analyses: List[Analysis] = store_with_case_and_analysis.get_analyses_by_case_entry_id(
        case_entry_id=case.id
    )
    # THEN one analysis should be returned
    for analysis in analyses:
        assert analysis
        assert analysis.family == case


def test_get_analyses_uploaded_to_vogue(
    store_with_analyses_for_cases: Store, case_id: str = "test_case_internal_id"
):
    """Test that an analysis can be fetched by case."""
    # GIVEN a database with an analysis and case

    # WHEN fetching the latest analysis to upload to vogue
    analyses: List[Analysis] = store_with_analyses_for_cases.get_analyses_for_vogue_upload()

    # THEN the analyses should not have been uploaded to Vogue
    for analysis in analyses:
        assert not analysis.uploaded_to_vogue_at


def test_get_analyses_uploaded_to_vogue_completed_before(
    store_with_analyses_for_cases: Store,
    timestamp_in_2_weeks: datetime,
):
    """Test that an analysis can be fetched by case."""
    # GIVEN a database with an analysis and case

    # WHEN fetching the latest analysis to upload to vogue that completed 2 weeks ago
    analyses: List[
        Analysis
    ] = store_with_analyses_for_cases.get_analysis_for_vogue_upload_completed_before(
        completed_at_before=timestamp_in_2_weeks
    )

    # THEN the returned analysis was completed earlier than 2 weeks ago
    for analysis in analyses:
        assert not analysis.uploaded_to_vogue_at
        assert analysis.completed_at < timestamp_in_2_weeks


def test_get_analyses_uploaded_to_vogue_completed_after(
    store_with_analyses_for_cases: Store,
    timestamp_yesterday: datetime,
):
    """Test get analysis to upload to vogue completed after.."""
    # GIVEN a database with an analysis and case

    # WHEN fetching the latest analysis to upload to vogue completed after yesterday
    analyses: List[
        Analysis
    ] = store_with_analyses_for_cases.get_analysis_for_vogue_upload_completed_after(
        completed_at_after=timestamp_yesterday
    )

    # THEN the returned analysis was completed after yesterday
    for analysis in analyses:
        assert not analysis.uploaded_to_vogue_at
        assert analysis.completed_at > timestamp_yesterday


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
    timestamp_now: datetime,
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
