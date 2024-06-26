from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


def get_case_message(case: Case) -> str:
    delivery_path: str = get_caesar_delivery_path(case)
    return (
        f"Hello,\n\n"
        f"The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path}"
    )


def get_cases_message(cases: list[Case]) -> str:
    delivery_path: str = get_caesar_delivery_path(cases[0])
    return (
        f"Hello,\n\n"
        f"The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
        f"{delivery_path}"
    )


class AnalysisMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        if len(cases) == 1:
            return get_case_message(cases[0])
        return get_cases_message(cases)
