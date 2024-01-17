from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_statina_batch_id
from cg.store.models import Case


class StatinaMessage(DeliveryMessage):
    def create_message(self, case: Case) -> str:
        batch_id: str = get_statina_batch_id(case)
        return f"Hello,\n\nBatch {batch_id} is now available in Statina."
