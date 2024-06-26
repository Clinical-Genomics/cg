from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


class FastqMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        return (
            f"Hello,\n\n"
            f"The fastq files for this order have been uploaded to your inbox on Caesar at:\n\n"
            f"{delivery_path}"
        )
