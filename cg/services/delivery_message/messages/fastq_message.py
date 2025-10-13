from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    REMINDER_TO_DOWNLOAD_MESSAGE,
    get_caesar_delivery_path,
)
from cg.store.models import Case


class FastqMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        sample_names: str = "\n".join([sample.name for case in cases for sample in case.samples])
        number_of_samples: int = sum(len(case.samples) for case in cases)
        sample_s_: str = "sample" if number_of_samples == 1 else "samples"
        return (
            f"Hello,\n\n"
            f"The fastq files for the following {sample_s_} have been uploaded to your inbox on Caesar:\n\n"
            f"{sample_names}\n\n"
            "Available under: \n\n"
            f"{delivery_path} \n\n"
            f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
        )
