from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


def get_cases_message(cases: list[Case]) -> str:
    delivery_path: str = get_caesar_delivery_path(cases[0])
    case_names: str = "\n".join([case.name for case in cases])
    case_s_: str = "case" if len(cases) == 1 else "cases"
    return (
        f"Hello,\n\n"
        f"The analysis files for the following {case_s_} are currently being uploaded to your inbox on Caesar:\n\n"
        f"{case_names}\n\n"
        f"Available under: \n\n"
        f"{delivery_path}"
    )


class AnalysisMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        return get_cases_message(cases)
