from cg.services.delivery_message.messages import DeliveryMessage
from cg.services.delivery_message.utils import get_fastq_delivery_path
from cg.store.models import Case


class FastqMessage(DeliveryMessage):
    def generate_message(self, case: Case):
        delivery_path: str = get_fastq_delivery_path(case)
        return (
            f"Hello,\n\n "
            f"The fastq files for this order have been uploaded to your inbox on Caesar at:\n\n"
            f"{delivery_path}"
        )
