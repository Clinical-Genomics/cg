import json
from datetime import datetime, timedelta
from unittest.mock import Mock, create_autospec

import pytest
from requests import Response

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.constants.constants import Workflow
from cg.exc import TrailblazerAPIHTTPError
from cg.services.mark_as_delivered_service import MarkAsDeliveredService
from cg.store.models import Analysis, Case, CaseSample, Order, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture
def trailblazer_id() -> int:
    return 666666


@pytest.fixture
def trailblazer_api() -> TypedMock[TrailblazerAPI]:
    """TrailblazerAPI for endpoints."""
    return create_typed_mock(TrailblazerAPI)


@pytest.fixture
def status_db() -> Store:
    """Store for endpoints."""
    return create_autospec(Store)


@pytest.fixture
def mark_as_delivered_service(
    trailblazer_api: TypedMock[TrailblazerAPI], status_db: Store
) -> MarkAsDeliveredService:
    return MarkAsDeliveredService(status_db=status_db, trailblazer_api=trailblazer_api.as_type)


def test_mark_analyses_success(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
):
    # GIVEN samples that should be delivered
    sample_1: Sample = create_autospec(Sample, delivered_at=None)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN two cases to be delivered
    case_1: Case = create_autospec(Case)
    case_sample_1 = create_autospec(
        CaseSample, case=case_1, sample=sample_1, should_deliver_sample=True
    )
    case_1.links = [case_sample_1]

    case_2: Case = create_autospec(Case)
    case_sample_2 = create_autospec(
        CaseSample, case=case_2, sample=sample_2, should_deliver_sample=True
    )
    case_2.links = [case_sample_2]

    # GIVEN an analysis linked to each case
    analysis_1: Analysis = create_autospec(Analysis, case=case_1, trailblazer_id=trailblazer_id)
    analysis_2: Analysis = create_autospec(Analysis, case=case_2, trailblazer_id=555555)

    # GIVEN a Trailblazer response
    tb_response = Response()
    tb_response.status_code = 200
    tb_response._content = json.dumps({"key": "value"}).encode("utf-8")
    trailblazer_api.as_type.set_analyses_delivery_status = Mock(return_value=tb_response)

    # WHEN we call mark_analyses
    response: Response = mark_as_delivered_service.mark_analyses([analysis_1, analysis_2])

    # THEN the samples should have been delivered
    assert sample_1.delivered_at is not None
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id, 555555], auth_token=None, signature=None
    )

    # THEN we should return the Trailblazer response
    assert response == tb_response


def test_mark_analyses_with_signature(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
):
    # GIVEN a signature and an analysis
    analysis = create_autospec(Analysis, trailblazer_id=trailblazer_id)

    # WHEN marking an analysis as delivered by a user
    mark_as_delivered_service.mark_analyses(analyses=[analysis], signature="CG")

    # THEN trailblazer should have been called with the user signature
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id], auth_token=None, signature="CG"
    )


def test_mark_analyses_mix_original_non_original_samples(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
):
    """Tests that delivering a case with a new sample and an existing sample will only deliver the new sample."""
    # GIVEN a new sample and an existing sample
    sample_new: Sample = create_autospec(Sample, delivered_at=None)
    sample_existing: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)

    case_sample_new = create_autospec(
        CaseSample, case=case, sample=sample_new, should_deliver_sample=True
    )
    case_sample_existing = create_autospec(
        CaseSample, case=case, sample=sample_existing, should_deliver_sample=False
    )
    case.links = [case_sample_new, case_sample_existing]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    mark_as_delivered_service.mark_analyses([analysis])

    # THEN only the new sample should be delivered
    assert sample_new.delivered_at is not None
    assert sample_existing.delivered_at is None

    # THEN endpoint in Trailblazer was called
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id], auth_token=None, signature=None
    )


def test_mark_analyses_rerun_case(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
):
    """Tests that delivering a case with already delivered samples does not deliver them again."""
    # GIVEN two already delivered samples
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=yesterday)

    # GIVEN a case with the two samples
    case: Case = create_autospec(Case)
    case_sample_1 = create_autospec(
        CaseSample, case=case, sample=sample_1, should_deliver_sample=True
    )
    case_sample_2 = create_autospec(
        CaseSample, case=case, sample=sample_2, should_deliver_sample=False
    )
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    mark_as_delivered_service.mark_analyses([analysis])

    # THEN the delivered_at for both samples should be untouched
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is yesterday

    # THEN endpoint in Trailblazer was called
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id], auth_token=None, signature=None
    )


def test_mark_analyses_mixed_delivered_at_original_samples(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
):
    """Tests that delivering a case with one already delivered original sample does not deliver that sample again."""
    # GIVEN one delivered sample and one undelivered sample
    yesterday = datetime.now() - timedelta(days=1)
    sample_1: Sample = create_autospec(Sample, delivered_at=yesterday)
    sample_2: Sample = create_autospec(Sample, delivered_at=None)

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, samples=[sample_1, sample_2])
    case_sample_1 = create_autospec(
        CaseSample, case=case, sample=sample_1, should_deliver_sample=True
    )
    case_sample_2 = create_autospec(
        CaseSample, case=case, sample=sample_2, should_deliver_sample=True
    )
    case.links = [case_sample_1, case_sample_2]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    mark_as_delivered_service.mark_analyses([analysis])

    # THEN only the delivered_at of the undelivered sample is updated
    assert sample_1.delivered_at is yesterday
    assert sample_2.delivered_at is not None

    # THEN endpoint in Trailblazer was called
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id], auth_token=None, signature=None
    )


@pytest.mark.parametrize("workflow", [Workflow.MICROSALT, Workflow.TAXPROFILER])
def test_mark_analyses_partial_delivery(
    trailblazer_api: TypedMock[TrailblazerAPI],
    mark_as_delivered_service: MarkAsDeliveredService,
    trailblazer_id: int,
    workflow: Workflow,
):
    """Test that delivering a case with a sample with not enough reads does not deliver that sample."""
    # GIVEN one delivered sample and one undelivered sample
    sample_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=11, is_negative_control=False
    )
    sample_not_enough_reads: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=10, reads=9, is_negative_control=False
    )

    # GIVEN that the two samples originally belong to this given case
    case: Case = create_autospec(Case, data_analysis=workflow)
    case_sample_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_enough_reads, should_deliver_sample=True
    )
    case_sample_not_enough_reads = create_autospec(
        CaseSample, case=case, sample=sample_not_enough_reads, should_deliver_sample=True
    )
    case.links = [case_sample_enough_reads, case_sample_not_enough_reads]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    mark_as_delivered_service.mark_analyses([analysis])

    # THEN only the delivered_at of the sample with enough reads is updated
    assert sample_enough_reads.delivered_at is not None
    assert sample_not_enough_reads.delivered_at is None

    # THEN endpoint in Trailblazer was called
    trailblazer_api.as_mock.set_analyses_delivery_status.assert_called_once_with(
        is_delivered=True, trailblazer_ids=[trailblazer_id], auth_token=None, signature=None
    )


def test_mark_analyses_trailblazer_error(
    status_db: Store,
    trailblazer_id: int,
):
    """Test that a TrailblazerAPIHTTPError is propagated from the service."""
    # GIVEN a TrailblazerAPI that fails
    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.set_analyses_delivery_status = Mock(side_effect=TrailblazerAPIHTTPError)

    # GIVEN a service that marks the analysis as delivered
    mark_as_delivered_service = MarkAsDeliveredService(
        status_db=status_db, trailblazer_api=trailblazer_api
    )

    # GIVEN a case to be delivered
    case: Case = create_autospec(Case)
    case.links = []

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    # THEN an error is raised
    with pytest.raises(TrailblazerAPIHTTPError):
        mark_as_delivered_service.mark_analyses([analysis])


def test_mark_analyses_negative_control(
    trailblazer_id: int, mark_as_delivered_service: MarkAsDeliveredService
):
    # GIVEN a negative control sample with lower reads than what the apptag expects
    negative_control_sample: Sample = create_autospec(
        Sample,
        delivered_at=None,
        expected_reads_for_sample=1000,
        is_negative_control=True,
        reads=9,
    )

    # GIVEN that its case-sample should deliver the sample
    case: Case = create_autospec(Case, data_analysis=Workflow.MICROSALT)
    case_sample_negative_control = create_autospec(
        CaseSample, case=case, sample=negative_control_sample, should_deliver_sample=True
    )
    case.links = [case_sample_negative_control]

    # GIVEN an analysis linked to the case
    analysis: Analysis = create_autospec(Analysis, case=case, trailblazer_id=trailblazer_id)

    # WHEN we call mark_analyses
    mark_as_delivered_service.mark_analyses([analysis])

    # THEN the sample should have a delivered_at set
    assert negative_control_sample.delivered_at is not None


def test_mark_analyses_two_cases_one_sample(mark_as_delivered_service: MarkAsDeliveredService):
    # GIVEN that a customer orders a case with a sample
    sample: Sample = create_autospec(
        Sample, delivered_at=None, expected_reads_for_sample=1, reads=1
    )
    case_1: Case = create_autospec(Case, internal_id="case_1", samples=[sample])
    case_sample_1: CaseSample = create_autospec(
        CaseSample, case=case_1, sample=sample, should_deliver_sample=True
    )
    case_1.links = [case_sample_1]
    order_1: Order = create_autospec(Order, cases=[case_1], is_open=True)

    # GIVEN that a customer orders a new case with the same sample (without the first case having been delivered)
    case_2: Case = create_autospec(Case, internal_id="case_2", samples=[sample])
    case_sample_2: CaseSample = create_autospec(
        CaseSample, case=case_2, sample=sample, should_deliver_sample=False
    )
    case_2.links = [case_sample_2]
    order_2: Order = create_autospec(Order, cases=[case_2], is_open=True)

    # GIVEN that sample is connected to both cases

    # GIVEN that the second order finishes first
    analysis: TrailblazerAnalysis = create_autospec(TrailblazerAnalysis, case_id="case_2")
    mark_as_delivered_service.trailblazer_api.get_delivered_analyses_for_order = Mock(
        return_value=[analysis]
    )

    # WHEN delivering the second order
    mark_as_delivered_service.close_order_in_status_db_if_closable(order_2)

    # THEN the first order should be open
    assert order_1.is_open

    # THEN the second order should be closed
    assert not order_2.is_open


def test_is_order_closable_true(mark_as_delivered_service: MarkAsDeliveredService):
    # GIVEN an open order with a case that includes only delivered samples
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=datetime.now())
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has a delivered analysis in Trailblazer
    analysis: TrailblazerAnalysis = create_autospec(TrailblazerAnalysis, case_id="case_id")
    mark_as_delivered_service.trailblazer_api.get_delivered_analyses_for_order = Mock(
        return_value=[analysis]
    )

    # WHEN checking if the order can be closed
    # THEN it returns True
    assert mark_as_delivered_service._is_order_closable(order)


def test_is_order_closeable_false_undelivered_samples(
    mark_as_delivered_service: MarkAsDeliveredService,
):
    # GIVEN an open order with a case that includes undelivered samples
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=None)
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has a delivered analysis in Trailblazer
    analysis: TrailblazerAnalysis = create_autospec(TrailblazerAnalysis, case_id="case_id")
    mark_as_delivered_service.trailblazer_api.get_delivered_analyses_for_order = Mock(
        return_value=[analysis]
    )

    # WHEN checking if the order can be closed
    # THEN it returns False
    assert not mark_as_delivered_service._is_order_closable(order)


def test_is_order_closeable_false_undelivered_analysis(
    mark_as_delivered_service: MarkAsDeliveredService,
):
    # GIVEN an open order with a case that includes only samples that have a delivered_at
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=datetime.now())
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has no delivered analyses in Trailblazer
    mark_as_delivered_service.trailblazer_api.get_delivered_analyses_for_order = Mock(
        return_value=[]
    )

    # WHEN checking if the order can be closed
    # THEN it returns False
    assert not mark_as_delivered_service._is_order_closable(order)
