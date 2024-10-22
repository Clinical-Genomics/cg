from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


class BamMessage(DeliveryMessage):

    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        return (
            f"Hello,\n\n"
            f"The following samples in this order have been sequenced:\n\n"
            f"{self.generate_sample_name_list(cases)}\n\n"
            f"The bam files have been uploaded to your inbox on Caesar at:\n\n"
            f"{delivery_path}"
        )

    @staticmethod
    def generate_sample_name_list(cases: list[Case]) -> str:
        return "\n".join([sample.name for case in cases for sample in case.samples])
