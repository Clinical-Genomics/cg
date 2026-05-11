from datetime import datetime
from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.services.deliver_service import DeliverService
from cg.store.models import Analysis, Case
from cg.store.store import Store


def test_deliver_case(mocker: MockerFixture):
    status_db = create_autospec(Store)
    not_uploaded_analysis = create_autospec(Analysis, uploaded_at=None)
    uploaded_analysis = create_autospec(Analysis, uploaded_at=datetime.now())
    case: Case = create_autospec(
        Case,
        analyses=[not_uploaded_analysis, uploaded_analysis],
    )
    status_db.get_case_by_internal_id_strict = Mock(return_value=case)

    #
    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_api.are_analyses_delivered = Mock(return_value=[(uploaded_analysis, False)])

    # GIVEN a deliver service
    deliver_service = DeliverService(status_db=status_db, trailblazer_api=trailblazer_api)
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")

    # WHEN delivering a case
    deliver_service.deliver_case("case_id")

    # THEN the analysis of the case should be marked as delivered
    mark_analyses_spy.assert_called_once_with([uploaded_analysis])
