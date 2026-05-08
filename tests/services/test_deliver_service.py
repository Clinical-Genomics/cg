from unittest.mock import Mock, create_autospec

from pytest_mock import MockerFixture

from cg.apps.tb.api import TrailblazerAPI
from cg.services.deliver_service import DeliverService
from cg.store.models import Case
from cg.store.store import Store


def test_deliver_case(mocker: MockerFixture):
    # GIVEN a deliver service
    status_db = create_autospec(Store)
    status_db.get_case_by_internal_id_strict = Mock(return_value=create_autospec(Case))
    deliver_service = DeliverService(status_db=create_autospec(Store), trailblazer_api=create_autospec(TrailblazerAPI))
    mark_analyses_spy = mocker.spy(deliver_service.mark_as_delivered_service, "mark_analyses")
    # WHEN delivering a case
    deliver_service.deliver_case("case_id")
    # THEN the analysis of the case should be marked as delivered
    mark_analyses_spy.assert_called_once_with(["case_id"])