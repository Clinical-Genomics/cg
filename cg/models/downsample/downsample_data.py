"""Model for down sampling meta data."""

import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import DataDelivery, Priority
from cg.store.models import ApplicationVersion, Case, Sample
from cg.store.store import Store
from cg.utils.calculations import multiply_by_million

LOG = logging.getLogger(__name__)


class DownsampleData:
    def __init__(
        self,
        status_db: Store,
        hk_api: HousekeeperAPI,
        sample_id: str,
        number_of_reads: float,
        case_id: str,
        case_name: str,
        out_dir: Path,
    ):
        """Initialize the downsample data and perform integrity checks."""
        self.status_db: Store = status_db
        self.housekeeper_api: HousekeeperAPI = hk_api
        self.sample_id: str = sample_id
        self.number_of_reads: float = number_of_reads
        self.case_id: str = case_id
        self.out_dir: Path = out_dir
        self.case_name: str = case_name
        self.original_sample: Sample = self.get_sample_to_downsample()
        self.original_case: Case = self.get_case_to_downsample()
        self.validate_enough_reads_to_downsample()
        self.downsampled_sample: Sample = self._generate_statusdb_downsampled_sample_record()
        self.downsampled_case: Case = self._generate_statusdb_downsampled_case()
        LOG.info(f"Downsample Data checks completed for {self.sample_id}")

    @property
    def downsampled_sample_name(
        self,
    ) -> str:
        """Return a new sample name with the number of reads to which it is down sampled in millions
        appended. DS stands for downsampled. The number of reads is converted to a string and the
        decimal point is replaced with a C."""
        return f"{self.sample_id}DS{self.convert_number_of_reads_to_string}M"

    @property
    def downsampled_case_name(
        self,
    ) -> str:
        """Return a case name with _downsampled appended."""
        return f"{self.case_name}-downsampled"

    @property
    def convert_number_of_reads_to_string(self) -> str:
        """Convert the number of reads to a string."""
        return str(self.number_of_reads).replace(".", "C")

    def get_sample_to_downsample(self) -> Sample:
        """
        Check if a sample exists in StatusDB.
        Raises:
            ValueError
        """
        sample: Sample = self.status_db.get_sample_by_internal_id(self.sample_id)
        if not sample:
            raise ValueError(f"Sample {self.sample_id} not found in StatusDB.")
        return sample

    def get_case_to_downsample(self) -> Case:
        """
        Check if a case exists in StatusDB.
            Raises: ValueError
        """
        case: Case = self.status_db.get_case_by_internal_id(self.case_id)
        if not case:
            raise ValueError(f"Case {self.case_id} not found in StatusDB.")
        return case

    def _generate_statusdb_downsampled_sample_record(
        self,
    ) -> Sample:
        """
        Generate a downsampled sample record for StatusDB.
        The new sample contains the original sample internal id and meta data.usDB
        """
        application_version: ApplicationVersion = self.get_application_version()
        downsampled_sample: Sample = self.status_db.add_sample(
            name=self.downsampled_sample_name,
            internal_id=self.downsampled_sample_name,
            sex=self.original_sample.sex,
            order=self.original_sample.order,
            reads=multiply_by_million(self.number_of_reads),
            downsampled_to=multiply_by_million(self.number_of_reads),
            from_sample=self.original_sample.internal_id,
            tumour=self.original_sample.is_tumour,
            priority=Priority.standard,
            customer=self.original_sample.customer,
            application_version=application_version,
            received=self.original_sample.received_at,
            prepared_at=self.original_sample.prepared_at,
            last_sequenced_at=self.original_sample.last_sequenced_at,
        )
        return downsampled_sample

    def _generate_statusdb_downsampled_case(
        self,
    ) -> Case:
        """Generate a case for the downsampled samples. The new case uses existing case data."""
        if self.status_db.case_with_name_exists(case_name=self.downsampled_case_name):
            return self.status_db.get_case_by_name(self.downsampled_case_name)
        downsampled_case: Case = self.status_db.add_case(
            data_analysis=self.original_case.data_analysis,
            data_delivery=DataDelivery.NO_DELIVERY,
            name=self.downsampled_case_name,
            panels=self.original_case.panels,
            priority=self.original_case.priority,
            ticket=self.original_case.latest_ticket,
        )
        downsampled_case.orders.append(self.original_case.latest_order)
        downsampled_case.customer = self.original_case.customer
        return downsampled_case

    def validate_enough_reads_to_downsample(self) -> None:
        """
        Check if the sample has enough reads to downsample.
        Raises:
            ValueError
        """
        if multiply_by_million(self.number_of_reads) > self.original_sample.reads:
            raise ValueError(
                f"Sample {self.original_sample.internal_id} does not have enough reads ({self.original_sample.reads}) to down sample to "
                f"{self.number_of_reads}M."
            )

    @property
    def fastq_file_input_directory(self) -> Path:
        """Get the latest version directory for a sample in housekeeper."""
        LOG.debug(
            f"Trying to get input fastq directory for {self.original_sample.internal_id} from Housekeeper."
        )
        return self.housekeeper_api.get_latest_bundle_version(
            bundle_name=self.original_sample.internal_id,
        ).full_path

    @property
    def fastq_file_output_directory(self):
        """Get the output directory for the downsampled sample."""
        return Path(self.out_dir, self.downsampled_sample.internal_id)

    def get_sample_status(
        self,
    ) -> str:
        """Return the status of a sample."""
        return self.original_sample.links[0].status if self.original_sample.links else "unknown"

    def get_application_version(self) -> ApplicationVersion:
        """Return the application version for a sample."""
        return self.original_sample.application_version

    def create_down_sampling_working_directory(self) -> Path:
        """
        Create a working directory for the downsample job.
        Raises:
            FileExistsError
        """
        working_directory: Path = self.fastq_file_output_directory
        if working_directory.exists():
            raise FileExistsError(f"Working directory {working_directory} already exists.")
        LOG.info(f"Creating working directory {working_directory}")
        working_directory.mkdir(parents=True, exist_ok=True)
        return working_directory
