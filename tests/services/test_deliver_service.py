from datetime import datetime
from unittest.mock import Mock, create_autospec

import pytest
from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import MultipleAnalysesToDeliverError, OrderNotFoundError, TrailblazerAPIHTTPError
from cg.services.deliver_service import DeliverService
from cg.store.models import Analysis, Case, Order
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


def test_deliver_case(mocker: MockerFixture):
    # GIVEN a case with two analyses
    status_db: Store = create_autospec(Store)
    not_uploaded_analysis = create_autospec(Analysis, trailblazer_id=1, uploaded_at=None)
    uploaded_analysis = create_autospec(Analysis, trailblazer_id=2, uploaded_at=datetime.now())
    case: Case = create_autospec(
        Case,
        analyses=[not_uploaded_analysis, uploaded_analysis],
    )
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    # GIVEN a Trailblazer API
    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.get_analyses_to_deliver_for_case = Mock(
        return_value=[create_autospec(TrailblazerAnalysis, id=2, delivered=False)]
    )

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")
    close_order_spy = mocker.spy(deliver_service.mark_as_delivered_service, "close_order")

    # WHEN delivering a case
    deliver_service.deliver_case(case_id="case_id", signature="CG")

    # THEN analysis that were not uploaded is filtered out
    trailblazer_api.get_analyses_to_deliver_for_case.assert_called_once_with("case_id")

    # THEN the analysis of the case should be marked as delivered
    mark_analyses_spy.assert_called_once_with(analyses=[uploaded_analysis], signature="CG")

    # THEN the order should have been closed
    close_order_spy.assert_called_once_with(order=uploaded_analysis.order)


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


def test_deliver_all_cases_success(mocker: MockerFixture):
    # GIVEN a TrailblazerAPI and a store
    status_db: Store = create_autospec(Store)
    order: Order = create_autospec(Order, is_open=True)
    analysis_to_deliver = create_autospec(
        Analysis, order=order, trailblazer_id=1, uploaded_at=datetime.now()
    )
    order.analyses = [analysis_to_deliver]
    status_db.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_analyses = [
        create_autospec(TrailblazerAnalysis, id=1),
        create_autospec(TrailblazerAnalysis, id=2),
    ]
    trailblazer_api.get_all_analyses_to_deliver = Mock(return_value=trailblazer_analyses)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_call = mocker.patch.object(
        deliver_service.mark_as_delivered_service, "mark_analyses"
    )
    mark_order_call = mocker.patch.object(deliver_service.mark_as_delivered_service, "close_order")

    # WHEN delivering all cases
    deliver_service.deliver_all_cases()

    # THEN it should get all analyses to deliver from Trailblazer
    trailblazer_api.get_all_analyses_to_deliver.assert_called_once()

    # THEN uploaded analyses should have been fetched from StatusDB
    status_db.get_uploaded_analyses.assert_called_once_with(trailblazer_ids=[1, 2])

    # THEN the analyses should have been marked as delivered
    mark_analyses_call.assert_called_once_with(analyses=[analysis_to_deliver])

    # THEN the order should have been closed
    mark_order_call.assert_called_once_with(order)


def test_deliver_all_cases_trailblazer_error(mocker: MockerFixture):
    # GIVEN a TrailblazerAPI and a store
    status_db: TypedMock[Store] = create_typed_mock(Store)
    analysis_to_deliver = create_autospec(Analysis, trailblazer_id=1, uploaded_at=datetime.now())
    status_db.as_type.get_uploaded_analyses = Mock(return_value=[analysis_to_deliver])
    trailblazer_api: TrailblazerAPI = create_autospec(TrailblazerAPI)
    trailblazer_analyses = [
        create_autospec(TrailblazerAnalysis, id=1),
    ]
    trailblazer_api.get_all_analyses_to_deliver = Mock(return_value=trailblazer_analyses)

    # GIVEN a Delivery Service
    deliver_service = DeliverService(status_db=status_db.as_type, trailblazer_api=trailblazer_api)

    # GIVEN the mark_analyses_call raises an TrailblazerAPIHTTPError
    mocker.patch.object(
        deliver_service.mark_as_delivered_service,
        "mark_analyses",
        side_effect=TrailblazerAPIHTTPError,
    )

    # WHEN delivering all analyses
    # THEN a TrailblazerAPIHTTPError is raised
    with pytest.raises(TrailblazerAPIHTTPError):
        deliver_service.deliver_all_cases()


def test_deliver_all_cases_no_analyses_to_deliver(mocker: MockerFixture):
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
    deliver_service.deliver_all_cases()

    # THEN it should get all analyses to deliver from Trailblazer
    trailblazer_api.as_mock.get_all_analyses_to_deliver.assert_called_once()

    # THEN uploaded analyses should have been fetched from StatusDB
    status_db.get_uploaded_analyses.assert_called_once()

    # THEN no call should have been made
    mark_analyses_call.assert_not_called()


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
    trailblazer_api.as_mock.get_analyses_to_deliver = Mock(
        return_value=[
            create_autospec(TrailblazerAnalysis, id=1),
            create_autospec(TrailblazerAnalysis, id=2),
        ]
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

    # THEN the uploded analyses should have been marked as delivered
    mark_analyses_call.assert_called_once_with(analyses=[analysis_1, analysis_2], signature="CG")

    # THEN the order should have been fetched from the database with the ticket id
    status_db.as_mock.get_order_by_ticket_id_strict.assert_called_once_with(123)

    # THEN uploaded analyses should have been fetched from the database with the trailblazer ids of the analyses to deliver
    status_db.as_mock.get_uploaded_analyses.assert_called_once_with([1, 2])

    # THEN the analyses to deliver should have been fetched from Trailblazer with the order id
    trailblazer_api.as_mock.get_analyses_to_deliver.assert_called_once_with(1)


def test_deliver_order_without_analyses(mocker: MockerFixture):
    # GIVEN a store with an order
    status_db: Store = create_autospec(Store)
    status_db.get_uploaded_analyses = Mock(return_value=[])

    # GIVEN a trailblazer api
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
