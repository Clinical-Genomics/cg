from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import (
    FreshdeskClosingTicketError,
    FreshdeskDeliveryMessageError,
    MultipleAnalysesToDeliverError,
    OrderNotFoundError,
    TrailblazerAnalysisDeliveryError,
    TrailblazerFailedToGetAnalysesError,
)
from cg.services.deliver_service import DeliverService
from cg.store.models import Analysis, Case, Order, Sample
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_deliver_case_closes_order(mocker: MockerFixture):
    # GIVEN a case with one analysis ready to be delivered
    analysis = create_autospec(
        Analysis,
        trailblazer_id=1,
        uploaded_at=datetime.now(),
    )
    case: Case = create_autospec(
        Case,
        analyses=[analysis],
        internal_id="case_id",
    )

    # GIVEN an open order with the case
    order: Order = create_autospec(Order, id=1, is_open=True, cases=[case])
    analysis.order = order
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a Trailblazer API with the analysis ready to be delivered
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    tb_analysis: TrailblazerAnalysis = create_autospec(
        TrailblazerAnalysis, id=1, delivered=False, case_id="case_id"
    )
    trailblazer_api.get_analyses_to_deliver_for_case = Mock(return_value=[tb_analysis])

    # GIVEN that the TB analysis is successfully delivered when delivering the case
    trailblazer_api.get_delivered_analyses_for_order = Mock(return_value=[tb_analysis])

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")

    # WHEN delivering a case
    deliver_service.deliver_case(case_id="case_id", signature="CG")

    # THEN the analysis of the case should be marked as delivered
    mark_analyses_spy.assert_called_once_with(analyses=[analysis], signature="CG")

    # THEN the order should have been closed
    assert not order.is_open


def test_deliver_case_order_is_not_closed(mocker: MockerFixture):
    # GIVEN a case with an analysis ready to be delivered
    uploaded_analysis = create_autospec(
        Analysis,
        id=2,
        trailblazer_id=2,
        uploaded_at=datetime.now(),
    )
    case_ready: Case = create_autospec(
        Case,
        analyses=[uploaded_analysis],
        internal_id="case_ready",
    )

    # GIVEN another case with an analysis that has not been uploaded and thus is not ready to be delivered
    not_uploaded_analysis = create_autospec(
        Analysis,
        id=1,
        trailblazer_id=1,
        uploaded_at=None,
    )
    case_not_ready: Case = create_autospec(
        Case,
        analyses=[not_uploaded_analysis],
        internal_id="case_not_ready",
    )

    # GIVEN an open order with the two cases
    order: Order = create_autospec(Order, id=1, is_open=True)
    order.cases = [case_not_ready, case_ready]
    not_uploaded_analysis.order = order
    uploaded_analysis.order = order

    # GIVEN a store for delivering the case that is ready to be delivered
    status_db: Store = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=case_ready)

    # GIVEN a Trailblazer API with the analysis of the case that is ready to be delivered
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    tb_uploaded_analysis: TrailblazerAnalysis = create_autospec(
        TrailblazerAnalysis, id=2, delivered=False, case_id="case_ready"
    )
    trailblazer_api.get_analyses_to_deliver_for_case = Mock(return_value=[tb_uploaded_analysis])

    # GIVEN that the TB analysis is successfully delivered when delivering the case
    trailblazer_api.get_delivered_analyses_for_order = Mock(return_value=[tb_uploaded_analysis])

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")

    # WHEN delivering the case that is ready to be delivered
    deliver_service.deliver_case(case_id="case_ready", signature="CG")

    # THEN analysis that were not uploaded is filtered out
    trailblazer_api.get_analyses_to_deliver_for_case.assert_called_once_with("case_ready")

    # THEN the analysis of the case should be marked as delivered
    mark_analyses_spy.assert_called_once_with(analyses=[uploaded_analysis], signature="CG")

    # THEN the order should have not been closed
    assert order.is_open


def test_deliver_case_more_than_one_found():
    # GIVEN store with a case
    status_db = create_autospec(Store)
    uploaded_analysis_one = create_autospec(Analysis, trailblazer_id=15, uploaded_at=datetime.now())
    uploaded_analysis_two = create_autospec(Analysis, trailblazer_id=16, uploaded_at=datetime.now())
    case: Case = create_autospec(
        Case,
        analyses=[uploaded_analysis_one, uploaded_analysis_two],
    )
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a Trailblazer API
    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.get_analyses_to_deliver_for_case = Mock(
        return_value=[
            create_autospec(TrailblazerAnalysis, id=15, delivered=False),
            create_autospec(TrailblazerAnalysis, id=16, delivered=False),
        ]
    )

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)

    # WHEN delivering a case
    # THEN a MultipleAnalysesToDeliverError is raised
    with pytest.raises(MultipleAnalysesToDeliverError):
        deliver_service.deliver_case(case_id="case_id", signature="email@cg.se")


def test_deliver_case_nothing_to_deliver(mocker: MockerFixture):
    # GIVEN store with a case
    status_db = create_autospec(Store)

    # GIVEN an analysis that has not been uploaded
    not_uploaded_analysis = create_autospec(Analysis, uploaded_at=None)

    # GIVEN an analysis that has been uploaded and delivered
    delivered_analysis = create_autospec(Analysis, trailblazer_id=15, uploaded_at=datetime.now())
    case: Case = create_autospec(
        Case,
        analyses=[not_uploaded_analysis, delivered_analysis],
    )
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a Trailblazer API
    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.get_analyses_to_deliver_for_case = Mock(return_value=[])

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")

    # WHEN delivering a case
    deliver_service.deliver_case(case_id="case_id", signature="email@cg.se")

    # THEN the MarkAsDeliver service is not called since there is nothing to deliver
    mark_analyses_spy.assert_not_called()


def test_deliver_all_available_success(mocker: MockerFixture):
    """
    Test that when delivering all available orders, it delivers the analyses
    that are ready to be delivered and attempts to close the orders.
    """

    # GIVEN one order in store with one analysis
    order_1: Order = create_autospec(Order, is_open=True)
    analysis_1 = create_autospec(
        Analysis, order=order_1, trailblazer_id=1, uploaded_at=datetime.now()
    )
    order_1.analyses = [analysis_1]

    # GIVEN another order in store with two analyses
    order_2: Order = create_autospec(Order, is_open=True)
    analysis_2 = create_autospec(
        Analysis, order=order_2, trailblazer_id=2, uploaded_at=datetime.now()
    )
    analysis_3 = create_autospec(
        Analysis, order=order_2, trailblazer_id=3, uploaded_at=datetime.now()
    )
    order_2.analyses = [analysis_2, analysis_3]

    # GIVEN that the three analyses are ready to be delivered
    status_db: Store = create_autospec(Store)
    status_db.get_uploaded_analyses = Mock(return_value=[analysis_1, analysis_2, analysis_3])

    # GIVEN a Trailblazer API
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)

    # GIVEN a Deliver Service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api.as_type)
    mark_analyses_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "mark_analyses"
    )
    close_order_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "close_order_in_status_db_if_closable"
    )
    delivery_message_spy = mocker.spy(deliver_service, "_freshdesk_send_delivery_message")
    close_ticket_spy = mocker.spy(deliver_service, "_freshdesk_close_ticket_if_open")

    # WHEN delivering all cases
    deliver_service.deliver_all_available()

    # THEN it should get all analyses to deliver from Trailblazer
    trailblazer_api.as_mock.get_all_analyses_to_deliver.assert_called_once()

    # THEN uploaded analyses should have been fetched from StatusDB
    status_db.get_uploaded_analyses.assert_called_once()

    # THEN the analyses of both orders should have been marked as delivered separately
    mark_analyses_call.assert_any_call(analyses=[analysis_1], signature=None)
    mark_analyses_call.assert_any_call(analyses=[analysis_2, analysis_3], signature=None)

    # THEN both orders should have been checked if they can be closed separately
    close_order_call.assert_any_call(order_1)
    close_order_call.assert_any_call(order_2)

    # THEN the delivery message should have been sent for both orders separately
    delivery_message_spy.assert_any_call(order=order_1, analyses=[analysis_1])
    delivery_message_spy.assert_any_call(order=order_2, analyses=[analysis_2, analysis_3])

    # THEN the ticket should have been closed for both orders separately
    close_ticket_spy.assert_any_call(order_1)
    close_ticket_spy.assert_any_call(order_2)


def test_deliver_all_available_no_analyses_to_deliver(mocker: MockerFixture):
    # GIVEN a TrailblazerAPI and a store without an analysis to deliver
    status_db: Store = create_autospec(Store)
    status_db.get_uploaded_analyses = Mock(return_value=[])
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api.as_type)
    mark_analyses_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "mark_analyses"
    )

    # WHEN delivering all cases
    deliver_service.deliver_all_available()

    # THEN it should get all analyses to deliver from Trailblazer
    trailblazer_api.as_mock.get_all_analyses_to_deliver.assert_called_once()

    # THEN uploaded analyses should have been fetched from StatusDB
    status_db.get_uploaded_analyses.assert_called_once()

    # THEN no call should have been made
    mark_analyses_call.assert_not_called()


def test_deliver_all_available_trailblazer_analysis_delivery_error(mocker: MockerFixture):
    # GIVEN a store with an analysis to deliver
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_to_deliver = create_autospec(
        Analysis, order=create_autospec(Order), trailblazer_id=1, uploaded_at=datetime.now()
    )
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])

    # GIVEN a Trailblazer API
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db.as_type, trailblazer_api=trailblazer_api)

    # GIVEN the MarkAsDeliveredService raises a TrailblazerAnalysisDeliveryError
    mocker.patch.object(
        deliver_service.mark_as_delivered_service,
        "mark_analyses",
        side_effect=TrailblazerAnalysisDeliveryError,
    )

    # WHEN delivering all analyses
    deliver_service.deliver_all_available()

    # THEN a rollback of statusdb is performed
    status_db.as_mock.rollback.assert_called_once()


def test_deliver_all_available_trailblazer_failed_to_get_analyses_error(mocker: MockerFixture):
    # GIVEN a store with an analysis to deliver
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_to_deliver = create_autospec(
        Analysis, order=create_autospec(Order), trailblazer_id=1, uploaded_at=datetime.now()
    )
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])

    # GIVEN a Trailblazer API
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db.as_type, trailblazer_api=trailblazer_api)

    # GIVEN the MarkAsDeliveredService raises a TrailblazerFailedToGetAnalysesError
    mocker.patch.object(
        deliver_service.mark_as_delivered_service,
        "_is_order_closable",
        side_effect=TrailblazerFailedToGetAnalysesError,
    )
    unmark_analysis_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "unmark_analyses"
    )

    # WHEN delivering all analyses
    deliver_service.deliver_all_available()

    # THEN a rollback of statusdb is performed
    status_db.as_mock.rollback.assert_called_once()

    # THEN the analysis should have been unmarked in Trailblazer
    unmark_analysis_call.assert_called_once_with([analysis_to_deliver])


def test_deliver_all_available_freshdesk_delivery_message_error(mocker: MockerFixture):
    # GIVEN a store with an analysis to deliver
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_to_deliver = create_autospec(
        Analysis, order=create_autospec(Order), trailblazer_id=1, uploaded_at=datetime.now()
    )
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])

    # GIVEN a Trailblazer API
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db.as_type, trailblazer_api=trailblazer_api)

    # GIVEN the _freshdesk_send_delivery_message method raises a FreshdeskDeliveryMessageError
    mocker.patch.object(
        deliver_service,
        "_freshdesk_send_delivery_message",
        side_effect=FreshdeskDeliveryMessageError,
    )
    unmark_analysis_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "unmark_analyses"
    )

    # WHEN delivering all analyses
    deliver_service.deliver_all_available()

    # THEN a rollback of statusdb is performed
    status_db.as_mock.rollback.assert_called_once()

    # THEN the analysis should have been unmarked in Trailblazer
    unmark_analysis_call.assert_called_once_with([analysis_to_deliver])


def test_deliver_all_available_freshdesk_closing_ticket_error(mocker: MockerFixture):
    # GIVEN a store with an analysis to deliver
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_to_deliver = create_autospec(
        Analysis, order=create_autospec(Order), trailblazer_id=1, uploaded_at=datetime.now()
    )
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])

    # GIVEN a Trailblazer API
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db.as_type, trailblazer_api=trailblazer_api)

    # GIVEN the _freshdesk_send_delivery_message method raises a FreshdeskClosingTicketError
    mocker.patch.object(
        deliver_service,
        "_freshdesk_close_ticket_if_open",
        side_effect=FreshdeskClosingTicketError,
    )

    # WHEN delivering all analyses
    deliver_service.deliver_all_available()

    # THEN the order should have been reopened if ever closed
    assert analysis_to_deliver.order.is_open

    # THEN a commit to the store is performed
    status_db.as_mock.commit_to_store.assert_called_once()


def test_deliver_order_success(mocker: MockerFixture):
    # GIVEN a store with an order
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_1 = create_autospec(Analysis, uploaded_at=datetime.now())
    analysis_2 = create_autospec(Analysis, uploaded_at=datetime.now())

    case_1: Case = create_autospec(
        Case,
        internal_id="case_1",
        analyses=[analysis_1],
    )
    case_2: Case = create_autospec(
        Case,
        internal_id="case_2",
        analyses=[analysis_2],
    )
    order: Order = create_autospec(Order, cases=[case_1, case_2], id=1)
    status_db.as_type.get_order_by_ticket_id_strict = Mock(return_value=order)
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_1, analysis_2])

    # GIVEN a Trailblazer API with two analyses to deliver for the order
    trailblazer_api: TypedMock[TrailblazerAPI] = create_typed_mock(TrailblazerAPI)
    tb_analysis_1: TrailblazerAnalysis = create_autospec(
        TrailblazerAnalysis, id=1, delivered=False, case_id="case_1"
    )
    tb_analysis_2: TrailblazerAnalysis = create_autospec(
        TrailblazerAnalysis, id=2, delivered=False, case_id="case_2"
    )
    trailblazer_api.as_mock.get_analyses_to_deliver = Mock(
        return_value=[tb_analysis_1, tb_analysis_2]
    )
    trailblazer_api.as_mock.get_delivered_analyses_for_order = Mock(
        return_value=[tb_analysis_1, tb_analysis_2]
    )

    # GIVEN a Delivery Service
    deliver_service = DeliverService(
        status_db=status_db.as_type, trailblazer_api=trailblazer_api.as_type
    )
    mark_analyses_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "mark_analyses"
    )

    # WHEN delivering the order
    deliver_service.deliver_order(ticket_id=123, signature="CG")

    # THEN the uploaded analyses should have been marked as delivered
    mark_analyses_call.assert_called_once_with(analyses=[analysis_1, analysis_2], signature="CG")

    # THEN the order should have been closed
    assert not order.is_open


def test_deliver_order_without_analyses(mocker: MockerFixture):
    # GIVEN a store with an open order without any analyses to deliver
    order: Order = create_autospec(Order, is_open=True)
    status_db: Store = create_autospec(Store)
    status_db.get_order_by_ticket_id_strict = Mock(return_value=order)
    status_db.get_uploaded_analyses = Mock(return_value=[])

    # GIVEN a Trailblazer API
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "mark_analyses"
    )

    # WHEN delivering an order
    deliver_service.deliver_order(ticket_id=666666, signature="CG")

    # THEN we should not have marked any analysis as delivered
    mark_analyses_call.assert_not_called()

    # THEN the order should have not been closed
    assert order.is_open


def test_deliver_order_invalid_ticket_id():
    # GIVEN an empty store
    status_db: Store = create_autospec(Store)
    status_db.get_order_by_ticket_id_strict = Mock(side_effect=OrderNotFoundError)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(
        status_db=status_db, trailblazer_api=create_autospec(TrailblazerAPI)
    )

    # WHEN delivering an order with a nonexisting ticket id
    # THEN an OrderNotFoundError was raised
    with pytest.raises(OrderNotFoundError):
        deliver_service.deliver_order(ticket_id=666666, signature="CG")


# TODO: move tests to mark as delivered service
def test_is_order_closable_true():
    # GIVEN an open order with a case that includes only delivered samples
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=datetime.now())
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has a delivered analysis in Trailblazer
    analysis: TrailblazerAnalysis = create_autospec(TrailblazerAnalysis, case_id="case_id")
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_api.get_delivered_analyses_for_order = Mock(return_value=[analysis])

    # GIVEN a DeliverService
    deliver_service = DeliverService(
        status_db=create_autospec(Store), trailblazer_api=trailblazer_api
    )

    # WHEN checking if the order can be closed
    # THEN it returns True
    assert deliver_service._is_order_closable(order)


def test_is_order_closeable_false_undelivered_samples():
    # GIVEN an open order with a case that includes undelivered samples
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=None)
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has a delivered analysis in Trailblazer
    analysis: TrailblazerAnalysis = create_autospec(TrailblazerAnalysis, case_id="case_id")
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_api.get_delivered_analyses_for_order = Mock(return_value=[analysis])

    # GIVEN a DeliverService
    deliver_service = DeliverService(
        status_db=create_autospec(Store), trailblazer_api=trailblazer_api
    )

    # WHEN checking if the order can be closed
    # THEN it returns False
    assert not deliver_service._is_order_closable(order)


def test_is_order_closeable_false_undelivered_analysis():
    # GIVEN an open order with a case that includes only samples that have a delivered_at
    sample_delivered1: Sample = create_autospec(Sample, delivered_at=datetime.now())
    sample_delivered2: Sample = create_autospec(Sample, delivered_at=datetime.now())
    case: Case = create_autospec(
        Case, samples=[sample_delivered1, sample_delivered2], internal_id="case_id"
    )
    order: Order = create_autospec(Order, cases=[case])

    # GIVEN that the case has no delivered analyses in Trailblazer
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_api.get_delivered_analyses_for_order = Mock(return_value=[])

    # GIVEN a DeliverService
    deliver_service = DeliverService(
        status_db=create_autospec(Store), trailblazer_api=trailblazer_api
    )

    # WHEN checking if the order can be closed
    # THEN it returns False
    assert not deliver_service._is_order_closable(order)
