from cg.constants.constants import Pipeline
from cg.exc import CaseNotFoundError
from cg.services.delivery_message.messages import DeliveryMessage, FastqMessage
from cg.store import Store
from cg.store.models import Case


message_map = {
    Pipeline.FASTQ: FastqMessage,
}


class DeliveryMessageService:
    def __init__(self, store: Store) -> None:
        self.store = store

    def get_delivery_message(self, case_id: str) -> str:
        case: Case | None = self.store.get_case_by_internal_id(case_id)
        if not case:
            raise CaseNotFoundError
        return self._get_message(case)

    def _get_message(self, case: Case) -> str:
        message: DeliveryMessage = message_map[case.data_analysis]()
        return message.generate_message(case)
