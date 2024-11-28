from abc import abstractmethod, ABC

from cg.services.delivery_message.messages.utils import (
    get_scout_links_row_separated,
    get_caesar_delivery_path,
)
from cg.store.models import Case


class RNAUploadMessageStrategy(ABC):
    """Abstract base class for delivery message strategies."""

    @abstractmethod
    def get_file_upload_message(self, delivery_path: str) -> str:
        """Generate the file upload message part."""
        pass


class RNAAnalysisStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return (
            f"The analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )


class RNAFastqAnalysisStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return (
            f"The fastq and analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )


class RNAFastqStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return (
            f"The fastq files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path}"
        )


class RNAScoutStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return ""  # No file upload message needed for this case.


class RNADeliveryMessage:
    def __init__(self, store, strategy: RNAUploadMessageStrategy):
        self.store = store
        self.strategy = strategy

    def create_message(self, cases: list[Case]) -> str:
        if len(cases) == 1:
            return self._get_case_message(cases[0])
        return self._get_cases_message(cases)

    def _get_case_message(self, case: Case) -> str:
        related_uploaded_dna_cases = self.store.get_uploaded_related_dna_cases(rna_case=case)
        scout_links = get_scout_links_row_separated(cases=related_uploaded_dna_cases)
        delivery_path = get_caesar_delivery_path(case)
        file_upload_message = self.strategy.get_file_upload_message(delivery_path)
        return (
            f"Hello,\n\n"
            f"The analysis for case {case.name} has been uploaded to the corresponding DNA case(s) on Scout at:\n\n"
            f"{scout_links}\n\n"
            f"{file_upload_message}"
        )

    def _get_cases_message(self, cases: list[Case]) -> str:
        message = "Hello,\n\n"
        for case in cases:
            related_uploaded_dna_cases = self.store.get_uploaded_related_dna_cases(rna_case=case)
            scout_links = get_scout_links_row_separated(cases=related_uploaded_dna_cases)
            message += (
                f"The analysis for case {case.name} has been uploaded to the corresponding DNA case(s) on Scout at:\n\n"
                f"{scout_links}\n\n"
            )
        delivery_path = get_caesar_delivery_path(cases[0])
        file_upload_message = self.strategy.get_file_upload_message(delivery_path)
        return message + file_upload_message
