from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_scout_link
from cg.store.models import Case


class ScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        scout_links: list[str] = [get_scout_link(case) for case in cases]
        scout_links_row_separated: str = "\n".join(scout_links)
        return f"Hello,\n\n The following cases has been uploaded to Scout:\n\n {scout_links_row_separated}"
