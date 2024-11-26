from cg.services.delivery_message.messages.delivery_message import DeliveryMessage
from cg.services.delivery_message.messages.utils import (
    get_caesar_delivery_path,
    get_scout_links_row_separated,
)
from cg.store.models import Case


class RNAAnalysisScoutMessage(DeliveryMessage):
    def __init__(self, store):
        super().__init__()
        self.store = store

    def create_message(self, cases: list[Case]) -> str:
        if len(cases) == 1:
            return self._get_case_message(cases[0])
        return self._get_cases_message(cases)

    def _get_case_message(self, case: Case) -> str:

        related_uploaded_dna_cases: list[Case] = self.store.get_uploaded_related_dna_cases(
            rna_case=case
        )
        scout_links_row_separated = get_scout_links_row_separated(cases=related_uploaded_dna_cases)

        delivery_path: str = get_caesar_delivery_path(case)
        return (
            f"Hello,\n\n"
            f"The analysis for case {case.name} has been uploaded to the corresponding DNA case(s) on Scout at:\n\n"
            f"{scout_links_row_separated}\n\n"
            f"The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )

    def _get_cases_message(self, cases: list[Case]) -> str:
        message: str = "Hello,\n\n"
        for case in cases:
            related_uploaded_dna_cases: list[Case] = self.store.get_uploaded_related_dna_cases(
                rna_case=case
            )
            scout_links_row_separated = get_scout_links_row_separated(
                cases=related_uploaded_dna_cases
            )

            message = (
                message
                + f"The analysis for case {case.name} has been uploaded to the corresponding DNA case(s) on Scout at:\n\n"
                + f"{scout_links_row_separated}\n\n"
            )

        delivery_path: str = get_caesar_delivery_path(cases[0])

        message = (
            message
            + "The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            + f"{delivery_path}"
        )

        return message
