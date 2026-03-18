from datetime import datetime, timedelta
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


def test_mark_analysis_mix_original_non_original_samples(trailblazer_id: int):
    """Tests that delivering a case with a new sample and an existing sample will only deliver the new sample."""
    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)

    # GIVEN a service that marks the analysis as delivered
    mark_as_delivered_service = MarkAsDeliveredService(
        status_db=status_db, trailblazer_api=analysis_client
    )

    # GIVEN a new sample and an existing sample
    sample_new: Sample = create_autospec(Sample, delivered_at=None)
    sample_existing: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)

    case_sample_new = create_autospec(CaseSample, case=case, sample=sample_new, is_original=True)
    case_sample_existing = create_autospec(
        CaseSample, case=case, sample=sample_existing, is_original=False
    )
    case.links = [case_sample_new, case_sample_existing]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    mark_as_delivered_service.mark_analysis(analysis)

    # THEN only the new sample should be delivered
    assert sample_new.delivered_at is not None
    assert sample_existing.delivered_at is None

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_rerun_case(trailblazer_id: int):
    """Tests that delivering a case with already delivered samples does not deliver them again."""
    # GIVEN a TrailblazerAPI
    analysis_client = create_autospec(AnalysisClient)

    # GIVEN a store
    status_db: FlaskStore = create_autospec(FlaskStore)

    # GIVEN a service that marks the analysis as delivered
    mark_as_delivered_service = MarkAsDeliveredService(
        status_db=status_db, trailblazer_api=analysis_client
    )

    # GIVEN two already delivered samples
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=yesterday)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=False)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    mark_as_delivered_service.mark_analysis(analysis)

    # THEN the delivered_at for both samples should be untouched
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is yesterday

    # THEN endpoint in Trailblazer was called
    analysis_client.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_mixed_delivered_at_original_samples(trailblazer_id: int):
    """Tests that delivering a case with one already delivered original sample does not deliver that sample again."""
    pass
