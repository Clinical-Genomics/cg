from cg.server.dto.delivery_message.delivery_message_request import (
    DeliveryMessageRequest,
)
from cg.server.dto.delivery_message.delivery_message_response import (
    DeliveryMessageResponse,
)
from cg.services.delivery_message.utils import get_message, validate_cases
from cg.store.models import Case
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_delivery_message(
        self, delivery_message_request: DeliveryMessageRequest
    ) -> DeliveryMessageResponse:
        case_ids: list[str] = delivery_message_request.case_ids
        cases: list[Case] = self.store.get_cases_by_internal_ids(case_ids)
        validate_cases(cases=cases, case_ids=case_ids)
        message: str = get_message(cases)
        return DeliveryMessageResponse(message=message)
