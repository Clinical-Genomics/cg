from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    get_caesar_delivery_path,
    get_pangolin_delivery_path,
)
from cg.store.models import Case


class CovidMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        pangolin_delivery_path: str = get_pangolin_delivery_path(cases[0])
        return (
            f"Hello,\n\n"
            f"The analysis is now complete.\n\n"
            f"The result files are being uploaded to Caesar at:\n\n"
            f"{delivery_path}\n\n"
            f"and the .csv files with pangolin-type have been sent to\n\n"
            f"{pangolin_delivery_path}"
        )
