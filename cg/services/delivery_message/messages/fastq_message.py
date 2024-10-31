from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


class FastqMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        case_names: str = "\n".join([case.name for case in cases])
        case_s_: str = "case" if len(cases) == 1 else "cases"
        return (
            f"Hello,\n\n"
            f"The fastq files for the following {case_s_} have been uploaded to your inbox on Caesar:\n\n"
            f"{case_names}\n"
            "Available under: \n\n"
            f"{delivery_path}"
        )
