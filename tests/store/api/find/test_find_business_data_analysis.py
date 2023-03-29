"""Tests the findbusinessdata part of the Cg store API related to Analysis model."""

from typing import List
from cg.store import Store
from cg.store.models import (
    Analysis,
)
from tests.store_helpers import StoreHelpers


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


def test_get_analyses_uploaded_to_vogue_with_completed_at(
    store_with_analyses_for_cases: Store, case_id: str = "test_case_internal_id"
):
    """Test that an analysis can be fetched by case."""
    # GIVEN a database with an analysis and case
