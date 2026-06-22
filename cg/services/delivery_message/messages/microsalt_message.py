from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    REMINDER_TO_DOWNLOAD_MESSAGE,
    get_caesar_delivery_path,
)
from cg.store.models import Case


class MicrosaltMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        return (
            f"Hello,<br><br>"
            f"The analysis is now complete and the fastq files are being uploaded to:<br><br>"
            f"{delivery_path} <br><br>"
            "The QC and Typing reports can be found attached. <br><br>"
            f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
            f"<br><br>it<br><br>worked"
        )
