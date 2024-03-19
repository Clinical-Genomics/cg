from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_statina_link
from cg.store.models import Case


class StatinaMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        batch_id: str = cases[0].name.split("-")[1]
        statina_link: str = get_statina_link(batch_id)
        return f"Hello,\n\nBatch {batch_id} is now available in Statina.\n\n{statina_link}"
