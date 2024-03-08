from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_statina_link
from cg.store.models import Case


class StatinaMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        statina_link: str = get_statina_link(cases[0])
        return f"Hello,\n\nBatch {statina_link} is now available in Statina."
