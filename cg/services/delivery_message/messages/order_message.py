from cg.constants import DataDelivery
from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_caesar_delivery_path
from cg.store.models import Case


class TaxprofilerDeliveryMessage(DeliveryMessage):

    FILE_TYPES_BY_DATA_DELIVERY_MAP: dict[DataDelivery, str] = {
        DataDelivery.FASTQ_ANALYSIS: "fastq and analysis",
        DataDelivery.ANALYSIS_FILES: DataDelivery.ANALYSIS_FILES,
    }

    def create_message(self, cases: list[Case]) -> str:
        delivery_path: str = get_caesar_delivery_path(cases[0])
        file_types: str = self.FILE_TYPES_BY_DATA_DELIVERY_MAP[cases[0].data_delivery]
        return (
            f"Hello,\n\n"
            f"The {file_types} files for this order are currently being uploaded to your inbox on Caesar at:\n\n"
            f"{delivery_path} \n\n"
        )
