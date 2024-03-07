from cg.exc import CaseNotFoundError, OrderMismatchError
from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.services.delivery_message.utils import get_message, is_matching_order
from cg.store.models import Case
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_delivery_message(
        self, delivery_message_request: DeliveryMessageRequest
    ) -> DeliveryMessageResponse:
        case_ids: list[str] = delivery_message_request.case_ids
        cases: list[Case] = []
        for case_id in case_ids:
            if case := self.store.get_case_by_internal_id(case_id):
                cases.append(case)
            else:
                raise CaseNotFoundError
        if not is_matching_order(cases):
            raise OrderMismatchError
        message: str = get_message(cases)
        return DeliveryMessageResponse(message=message)
