from unittest.mock import create_autospec

import pytest

from cg.server.ext import AnalysisClient, FlaskStore
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, CaseSample, Sample


@pytest.fixture
def trailblazer_id() -> int:
    return 666666


def test_mark_analysis(trailblazer_id: int):
    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)

    # GIVEN a service that marks the analysis as delivered
    mark_as_delivered_service = MarkAsDeliveredService(
        status_db=status_db, trailblazer_api=analysis_client
    )

    # GIVEN samples that should be delivered
    sample_1: Sample = create_autospec(Sample, delivered_at=None)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case)
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=True)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    mark_as_delivered_service.mark_analysis(analysis)

    # THEN the samples should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )
