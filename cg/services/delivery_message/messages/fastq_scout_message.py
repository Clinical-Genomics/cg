from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    get_fastq_delivery_path,
    get_scout_link,
)
from cg.store.models import Case


def get_case_message(scout_link: str, delivery_path) -> str:
    return (
        f"Hello,\n\n "
        f"The results have been uploaded to Scout for the following case::\n\n"
        f"{scout_link}\n\n"
        f"The fastq files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path}"
    )


def get_cases_message(scout_links: str, delivery_path) -> str:
    return (
        f"Hello,\n\n "
        f"The results have been uploaded to Scout for the following case::\n\n"
        f"{scout_links}\n\n"
        f"The fastq files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path}"
    )


class FastqScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        scout_links: list[str] = [get_scout_link(case) for case in cases]
        scout_links_row_separated: str = "\n".join(scout_links)
        delivery_path: str = get_fastq_delivery_path(cases[0])
        if len(cases) == 1:
            return get_case_message(
                scout_link=scout_links_row_separated, delivery_path=delivery_path
            )
        return get_cases_message(scout_links=scout_links_row_separated, delivery_path=delivery_path)
