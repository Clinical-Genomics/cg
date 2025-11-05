from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    REMINDER_TO_DOWNLOAD_MESSAGE,
    get_caesar_delivery_path,
    get_scout_link,
)
from cg.store.models import Case


def get_case_message(case: Case) -> str:
    scout_link: str = get_scout_link(case)
    delivery_path: str = get_caesar_delivery_path(case)
    return (
        "Hello,\n\n"
        "The analysis has been uploaded to Scout for the following case:\n\n"
        f"{scout_link}\n\n"
        "The raw data files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path} \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


def get_cases_message(cases: list[Case]) -> str:
    scout_links: list[str] = [get_scout_link(case) for case in cases]
    scout_links_row_separated: str = "\n".join(scout_links)
    delivery_path: str = get_caesar_delivery_path(cases[0])
    return (
        "Hello,\n\n "
        "The analyses have been uploaded to Scout for the following cases:\n\n"
        f"{scout_links_row_separated}\n\n"
        "The raw data files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path} \n\n"
        f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
    )


class RawDataScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        if len(cases) == 1:
            return get_case_message(cases[0])
        return get_cases_message(cases)
