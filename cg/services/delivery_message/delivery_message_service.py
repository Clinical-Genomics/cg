from cg.apps.tb import TrailblazerAPI
from cg.apps.tb.models import TrailblazerAnalysis
from cg.exc import OrderNotDeliverableError, OrderNotFoundError
from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.services.delivery_message.utils import get_message, validate_cases
from cg.store.models import Case, Order
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.store = store
        self.trailblazer_api = trailblazer_api

    def get_cases_message(
        self, delivery_message_request: DeliveryMessageRequest
    ) -> DeliveryMessageResponse:
        case_ids: list[str] = delivery_message_request.case_ids
        return self._get_delivery_message(set(case_ids))

    def get_order_message(self, order_id: int) -> DeliveryMessageResponse:
        order: Order = self.store.get_order_by_id(order_id)
        if not order:
            raise OrderNotFoundError(f"Order with ID {order_id} not found.")
        analyses: list[TrailblazerAnalysis] = self.trailblazer_api.get_analyses_to_deliver(order_id)
        if not analyses:
            raise OrderNotDeliverableError(
                f"No analyses ready to be delivered for order {order_id}"
            )
        case_ids: set[str] = {analysis.case_id for analysis in analyses}
        return self._get_delivery_message(case_ids)

    def _get_delivery_message(self, case_ids: set[str]):
        cases: list[Case] = self.store.get_cases_by_internal_ids(case_ids)
        validate_cases(cases=cases, case_ids=case_ids)
        message: str = get_message(cases)
        return DeliveryMessageResponse(message=message)
