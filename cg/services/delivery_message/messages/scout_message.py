from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_scout_link
from cg.store.models import Case


class ScoutMessage(DeliveryMessage):
    def create_message(self, case: Case) -> str:
        scout_link: str = get_scout_link(case)
        return f"Hello,\n\n The following case has been uploaded to Scout:\n\n {scout_link}"
