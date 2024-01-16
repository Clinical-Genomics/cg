from cg.exc import CaseNotFoundError
from cg.services.delivery_message.utils import get_message
from cg.store import Store


class DeliveryMessageService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_delivery_message(self, case_id: str) -> str:
        if case := self.store.get_case_by_internal_id(case_id):
            return get_message(case)
        else:
            raise CaseNotFoundError
