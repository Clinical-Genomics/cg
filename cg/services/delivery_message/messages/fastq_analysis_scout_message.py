from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    get_fastq_delivery_path,
    get_scout_link,
)
from cg.store.models import Case


class FastqAnalysisScoutMessage(DeliveryMessage):
    def create_message(self, cases: list[Case]) -> str:
        scout_links: list[str] = [get_scout_link(case) for case in cases]
        scout_links_row_separated: str = "\n".join(scout_links)
        delivery_path: str = get_fastq_delivery_path(cases[0])
        return (
            f"Hello,\n\n "
            f"The results have been uploaded to Scout for the following cases:\n\n"
            f"{scout_links_row_separated}\n\n"
            f"The fastq and analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )
