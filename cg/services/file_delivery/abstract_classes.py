from abc import abstractmethod, ABC


class FilterDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for filtering files to deliver.
    """

    @abstractmethod
    def filter_files(self, case_id: str) -> None:
        """Filter the files to deliver."""
        pass


class FormatDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for formatting files to deliver.
    """

    @abstractmethod
    def format_files(self, case_id: str) -> None:
        """Format the files to deliver."""
        pass


class MoveDeliveryFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for moving files to the customer folder. including formatting and renaming.
    """

    @abstractmethod
    def move_files(self, case_id: str) -> None:
        """Move the files to the customer folder."""
        pass


class GenerateDeliveryReportFilesService(ABC):
    """
    Abstract class that encapulates the logic required for generating a report of the files to deliver.
    """

    @abstractmethod
    def generate_report(self, case_id: str) -> None:
        """Generate a report of the files to deliver and adds it to housekeeper."""
        pass


class DeliverFilesService(ABC):
    """
    Abstract class that encapsulates the logic required for delivering files to the customer.

    1. Get the files to deliver from Housekeeper based on workflow and data file_delivery
    2. Create a file_delivery folder structure in the customer folder on Hasta and move the files there
    3. Reformatting of output / renaming of files
    4. Start a Rsync job to upload the files to Caesar
    5. Track the status of the Rsync job in Trailblazer
    """

    @abstractmethod
    def __init__(
        self,
        delivery_file_manager_service: FetchDeliveryFilesService,
        move_file_service: MoveDeliveryFilesService,
    ):
        self.file_manager = delivery_file_manager_service
        self.file_mover = move_file_service

    @abstractmethod
    def deliver_files_for_case(self, case_id: str) -> None:
        """Deliver the files to the customer folder."""
        pass
