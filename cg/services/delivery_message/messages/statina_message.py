from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.store.models import Case


class StatinaMessage(DeliveryMessage):
    def create_message(self, case: Case) -> str:
        return f"Hello,\n\nBatch BATCH_ID is now available in Statina."
