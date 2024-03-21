from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_scout_link
from cg.store.models import Case


def get_case_message(case: Case) -> str:
    scout_link: str = get_scout_link(case)
    return (
        f"Hello,\n\nThe analysis has been uploaded to Scout for the following case:\n\n{scout_link}"
    )


def get_cases_message(cases: list[Case]) -> str:
    scout_links: list[str] = [get_scout_link(case) for case in cases]
    scout_links_row_separated: str = "\n".join(scout_links)
    return f"Hello,\n\nThe analyses of the following cases have been uploaded to Scout:\n\n{scout_links_row_separated}"


class ScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        if len(cases) == 1:
            return get_case_message(cases[0])
        return get_cases_message(cases)
