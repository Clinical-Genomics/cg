from cg.apps.tb import TrailblazerAPI
from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.services.delivery_message.utils import (
    get_cases_ready_for_delivery,
    get_message,
    validate_cases,
)
from cg.store.models import Case, Order
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store, trailblazer_api: TrailblazerAPI) -> None:
        self.store = store
        self.trailblazer_api = trailblazer_api

    def get_delivery_message(
        self, delivery_message_request: DeliveryMessageRequest
    ) -> DeliveryMessageResponse:
        case_ids: list[str] = delivery_message_request.case_ids
        cases: list[Case] = self.store.get_cases_by_internal_ids(case_ids)
        validate_cases(cases=cases, case_ids=case_ids)
        message: str = get_message(cases)
        return DeliveryMessageResponse(message=message)

    def get_delivery_message_for_order(self, order_id: int) -> DeliveryMessageResponse:
        order: Order = self.store.get_order_by_id(order_id)
        cases_ready_for_delivery: list[Case] = get_cases_ready_for_delivery(
            order=order, trailblazer_api=self.trailblazer_api
        )
        case_ids: list[str] = [case.internal_id for case in cases_ready_for_delivery]
        return self.get_delivery_message(DeliveryMessageRequest(case_ids=case_ids))
