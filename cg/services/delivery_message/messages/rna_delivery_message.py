from abc import ABC, abstractmethod

from cg.services.delivery_message.messages.utils import (
    REMINDER_TO_DOWNLOAD_MESSAGE,
    get_caesar_delivery_path,
    get_scout_links_row_separated,
)
from cg.store.models import Case
from cg.store.store import Store


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
            f"{delivery_path} \n\n"
            f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
        )


class RNAFastqAnalysisStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return (
            f"The fastq and analysis files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path} \n\n"
            f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
        )


class RNAFastqStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return (
            f"The fastq files are currently being uploaded to your inbox on Caesar:\n\n"
            f"{delivery_path} \n\n"
            f"{REMINDER_TO_DOWNLOAD_MESSAGE}"
        )


class RNAScoutStrategy(RNAUploadMessageStrategy):
    def get_file_upload_message(self, delivery_path: str) -> str:
        return ""  # No file upload message needed for this case.


class RNADeliveryMessage:
    def __init__(self, store: Store, strategy: RNAUploadMessageStrategy):
        self.store = store
        self.strategy = strategy

    def create_message(self, cases: list[Case]) -> str:
        message = "Hello,\n\n"
        for case in cases:
            scout_message: str = self._get_scout_message_for_case(case=case)
            message += scout_message
        delivery_path: str = get_caesar_delivery_path(cases[0])
        file_upload_message: str = self.strategy.get_file_upload_message(delivery_path)
        return message + file_upload_message

    def _get_scout_message_for_case(self, case: Case) -> str:
        related_uploaded_dna_cases: list[Case] = self.store.get_uploaded_related_dna_cases(
            rna_case=case
        )
        scout_links: str = get_scout_links_row_separated(cases=related_uploaded_dna_cases)
        return (
            f"The analysis for case {case.name} has been uploaded to the corresponding DNA case(s) on Scout at:\n\n"
            f"{scout_links}\n\n"
        )
