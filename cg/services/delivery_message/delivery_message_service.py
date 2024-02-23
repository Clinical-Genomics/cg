from cg.exc import CaseNotFoundError
from cg.server.dto.delivery_message_response import DeliveryMessageResponse
from cg.services.delivery_message.utils import get_message
from cg.store.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_delivery_message(self, case_id: str) -> DeliveryMessageResponse:
        if case := self.store.get_case_by_internal_id(case_id):
            message: str = get_message(case)
            return DeliveryMessageResponse(message=message)
        else:
            raise CaseNotFoundError
