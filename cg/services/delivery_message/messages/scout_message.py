from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_scout_link
from cg.store.models import Case


def get_case_message(scout_link: str) -> str:
    return f"Hello,\n\n The following case has been uploaded to Scout:\n\n {scout_link}"


def get_cases_message(scout_links: str) -> str:
    return f"Hello,\n\n The following cases has been uploaded to Scout:\n\n {scout_links}"


class ScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        scout_links: list[str] = [get_scout_link(case) for case in cases]
        scout_links_row_separated: str = "\n".join(scout_links)
        if len(cases) == 1:
            return get_case_message(scout_links_row_separated)
        return get_cases_message(scout_links_row_separated)
