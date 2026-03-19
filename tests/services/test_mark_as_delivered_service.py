from datetime import datetime, timedelta
from unittest.mock import Mock, create_autospec

import pytest

from cg.constants.constants import Workflow
from cg.exc import TrailblazerAPIHTTPError
from cg.server.ext import AnalysisClient, FlaskStore
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, CaseSample, Sample
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def trailblazer_id() -> int:
    return 666666


@pytest.fixture
def analysis_client() -> TypedMock[AnalysisClient]:
    """TrailblazerAPI for endpoints."""
    return create_typed_mock(AnalysisClient)


@pytest.fixture
def status_db() -> FlaskStore:
    """Store for endpoints."""
    return create_autospec(FlaskStore)


@pytest.fixture
def mark_as_delivered_service(
    analysis_client: TypedMock[AnalysisClient], status_db: FlaskStore
) -> MarkAsDeliveredService:
    return MarkAsDeliveredService(status_db=status_db, trailblazer_api=analysis_client.as_type)


def test_mark_analysis(
    analysis_client: TypedMock[AnalysisClient],
    mark_as_delivered_service: MarkAsDeliveredService,
    status_db: FlaskStore,
    trailblazer_id: int,
):
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
    mark_as_delivered_service._mark_analysis(analysis)

    # THEN the samples should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.as_mock.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_mix_original_non_original_samples(
    analysis_client: TypedMock[AnalysisClient],
    mark_as_delivered_service: MarkAsDeliveredService,
    status_db: FlaskStore,
    trailblazer_id: int,
):
    """Tests that delivering a case with a new sample and an existing sample will only deliver the new sample."""
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
    mark_as_delivered_service._mark_analysis(analysis)

    # THEN only the new sample should be delivered
    assert sample_new.delivered_at is not None
    assert sample_existing.delivered_at is None

    # THEN endpoint in Trailblazer was called
    analysis_client.as_mock.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_rerun_case(
    analysis_client: TypedMock[AnalysisClient],
    mark_as_delivered_service: MarkAsDeliveredService,
    status_db: FlaskStore,
    trailblazer_id: int,
):
    """Tests that delivering a case with already delivered samples does not deliver them again."""
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
    mark_as_delivered_service._mark_analysis(analysis)

    # THEN the delivered_at for both samples should be untouched
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is yesterday

    # THEN endpoint in Trailblazer was called
    analysis_client.as_mock.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_mixed_delivered_at_original_samples(
    analysis_client: TypedMock[AnalysisClient],
    mark_as_delivered_service: MarkAsDeliveredService,
    status_db: FlaskStore,
    trailblazer_id: int,
):
    """Tests that delivering a case with one already delivered original sample does not deliver that sample again."""
    # GIVEN one delivered sample and one undelivered sample
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])
    case_sample_1 = create_autospec(CaseSample, case=case, sample=sample_1, is_original=True)
    case_sample_2 = create_autospec(CaseSample, case=case, sample=sample_2, is_original=True)
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    mark_as_delivered_service._mark_analysis(analysis)

    # THEN only the delivered_at of the undelivered sample is updated
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    analysis_client.as_mock.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


@pytest.mark.parametrize("workflow", [Workflow.MICROSALT, Workflow.TAXPROFILER])
def test_mark_analysis_partial_delivery(
    analysis_client: TypedMock[AnalysisClient],
    mark_as_delivered_service: MarkAsDeliveredService,
    status_db: FlaskStore,
    trailblazer_id: int,
    workflow: Workflow,
):
    """Test that delivering a case with a sample with not enough reads does not deliver that sample."""
    # GIVEN one delivered sample and one undelivered sample
    sample_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=11
    )
    sample_not_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=9
    )

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, data_analysis=workflow)
    case_sample_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_enough_reads, is_original=True
    )
    case_sample_not_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_not_enough_reads, is_original=True
    )
    case.links = [case_sample_enough_reads, case_sample_not_enough_reads]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    mark_as_delivered_service._mark_analysis(analysis)

    # THEN only the delivered_at of the sample with enough reads is updated
    assert sample_enough_reads.delivered_at is not None
    assert sample_not_enough_reads.delivered_at is None

    # THEN endpoint in Trailblazer was called
    analysis_client.as_mock.mark_analyses_as_delivered.assert_called_once_with(
        trailblazer_ids=[trailblazer_id]
    )


def test_mark_analysis_trailblazer_error(
    status_db: FlaskStore,
    trailblazer_id: int,
):
    """Test that a TrailblazerAPIHTTPError is propagated from the service."""
    # GIVEN a TrailblazerAPI that fails
    analysis_client = create_autospec(AnalysisClient)
    analysis_client.mark_analyses_as_delivered = Mock(side_effect=TrailblazerAPIHTTPError)

    # GIVEN a service that marks the analysis as delivered
    mark_as_delivered_service = MarkAsDeliveredService(
        status_db=status_db, trailblazer_api=analysis_client
    )

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case)
    case.links = []

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analysis
    # THEN an error is raised
    with pytest.raises(TrailblazerAPIHTTPError):
        mark_as_delivered_service._mark_analysis(analysis)
