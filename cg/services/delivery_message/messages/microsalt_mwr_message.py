from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_fastq_delivery_path
from cg.store.models import Case


class MicrosaltMwrMessage(DeliveryMessage):
    def create_message(self, case: Case) -> str:
        delivery_path: str = get_fastq_delivery_path(case)
        return (
            f"Hello,\n\n "
            f"The analysis is now complete and the fastq files are being uploaded to:\n\n"
            f"{delivery_path} \n\n"
            "The QC and Typing reports can be found attached."
        )
