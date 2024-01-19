from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import get_fastq_delivery_path, get_scout_link
from cg.store.models import Case


class AnalysisScoutMessage(DeliveryMessage):
    def create_message(self, case: Case) -> str:
        scout_link: str = get_scout_link(case)
        delivery_path: str = get_fastq_delivery_path(case)
        return (
            f"Hello,\n\n "
            f"The results have been uploaded to Scout for the following case:\n\n"
            f"{scout_link}\n\n"
            f"The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )
