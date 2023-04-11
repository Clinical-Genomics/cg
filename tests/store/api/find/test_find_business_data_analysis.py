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


def test_get_latest_nipt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_fluffy: Store, timestamp_now: datetime
):
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN calling the analyses_to_delivery_report
    analyses = (
        store_with_analyses_for_cases_not_uploaded_fluffy.get_latest_nipt_analysis_to_upload()
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.family.internal_id in ["test_case_1", "yellowhog"]
        assert analysis.started_at == timestamp_now
        assert analysis.uploaded_at is None
        assert analysis.pipeline == Pipeline.FLUFFY


def test_get_latest_microsalt_analysis_to_upload(
    store_with_analyses_for_cases_not_uploaded_microsalt: Store,
    timestamp_now: datetime,
    pipeline: Pipeline = Pipeline.MICROSALT,
):
    # GIVEN an analysis that is not delivery reported but there exists a newer analysis

    # WHEN calling the analyses_to_delivery_report
    analyses = (
        store_with_analyses_for_cases_not_uploaded_microsalt.get_latest_microsalt_analysis_to_upload()
    )

    # THEN only the newest analysis should be returned
    for analysis in analyses:
        assert analysis.family.internal_id in ["test_case_1", "yellowhog"]
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


def test_get_analyses(store_with_analyses_for_cases: Store, analysis_id: int = 1):
    """Test all analyses can be returned."""
    # GIVEN a database with an analysis and case

    # WHEN fetching all analyses
    analysis: List[Analysis] = store_with_analyses_for_cases.get_analyses()

    # THEN one analysis should be returned
    assert len(analysis) == store_with_analyses_for_cases._get_query(table=Analysis).count()
