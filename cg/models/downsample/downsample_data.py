"""Model for down sampling meta data."""
import logging
from pathlib import Path

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import Priority, SequencingFileTag
from cg.store import Store
from cg.store.models import ApplicationVersion, Family, Sample
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
    ):
        """Initialize the downsample data and perform integrity checks.
        Raises:
            ValueError
            FileExistsError
        """
        self.status_db: Store = status_db
        self.housekeeper_api: HousekeeperAPI = hk_api
        self.sample_id: str = sample_id
        self.number_of_reads: float = number_of_reads
        self.case_id: str = case_id
        self.original_sample: Sample = self.get_sample_to_downsample()
        self.original_case: Family = self.get_case_to_downsample()
        self.has_enough_reads: bool = self.has_enough_reads_to_downsample()
        self.downsampled_sample: Sample = self._generate_statusdb_downsampled_sample_record()
        self.downsampled_case: Family = self._generate_statusdb_downsampled_case()
        self.create_down_sampling_working_directory()
        LOG.info(f"Downsample Data checks completed for {self.sample_id}")

    @property
    def downsampled_sample_name(
        self,
    ) -> str:
        """Return a new sample name with the number of reads to which it is down sampled in millions appended."""
        new_name: str = f"{self.sample_id}_{self.number_of_reads}M"
        LOG.info(f"Changed {self.sample_id} to {new_name}")
        return new_name

    @property
    def downsampled_case_name(
        self,
    ) -> str:
        """Return a case name with _downsampled appended."""
        new_name: str = f"{self.case_id}_downsampled"
        LOG.info(f"Changed {self.case_id} to {new_name}")
        return new_name

    def get_sample_to_downsample(self) -> Sample:
        """Check if a sample exists in StatusDB."""
        sample: Sample = self.status_db.get_sample_by_internal_id(self.sample_id)
        if not sample:
            raise ValueError(f"Sample {self.sample_id} not found in StatusDB.")
        return sample

    def get_case_to_downsample(self) -> Family:
        """Check if a case exists in StatusDB."""
        case: Family = self.status_db.get_case_by_internal_id(self.case_id)
        if not case:
            raise ValueError(f"Case {self.case_id} not found in StatusDB.")
        return case

    def _generate_statusdb_downsampled_sample_record(
        self,
    ) -> Sample:
        """
        Generate a downsampled sample record for StatusDB.
        The new sample contains the original sample internal id and meta data.
        Raises:
            ValueError if the downsampled sample already exists in statusDB
        """
        application_version: ApplicationVersion = self.get_application_version(self.original_sample)
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
        )
        return downsampled_sample

    def _generate_statusdb_downsampled_case(
        self,
    ) -> Family:
        """Generate a case for the downsampled samples. The new case uses existing case data."""
        downsampled_case: Family = self.status_db.add_case(
            data_analysis=self.original_case.data_analysis,
            data_delivery=self.original_case.data_delivery,
            name=self.downsampled_case_name,
            panels=self.original_case.panels,
            priority=self.original_case.priority,
            ticket=self.original_case.latest_ticket,
        )
        downsampled_case.customer = self.original_case.customer

        return downsampled_case

    def has_enough_reads_to_downsample(self) -> bool:
        """Check if the sample has enough reads to downsample."""
        if not self.original_sample.reads > multiply_by_million(self.number_of_reads):
            raise ValueError(
                f"Sample {self.original_sample.internal_id} does not have enough reads ({self.original_sample.reads}) to down sample to "
                f"{self.number_of_reads}M."
            )
        return True

    @property
    def fastq_file_input_directory(self) -> Path:
        """Get the latest version directory for a sample in housekeeper."""
        return Path(
            self.housekeeper_api.get_file_from_latest_version(
                bundle_name=self.original_sample.internal_id, tags={SequencingFileTag.FASTQ}
            ).path
        ).parent

    @property
    def fastq_file_output_directory(self):
        """Get the output directory for the downsampled sample."""
        ## TO DO add path to config in servers
        return Path("home", "proj", "stage", "downsample", self.downsampled_sample.internal_id)

    @staticmethod
    def sample_status(sample: Sample) -> str:
        """Return the status of a sample."""
        return sample.links[0].status if sample.links else "unknown"

    @staticmethod
    def get_application_tag(sample: Sample) -> str:
        """Return the application for a sample."""
        return sample.application_version.application.tag

    def get_application_version(self, sample: Sample) -> ApplicationVersion:
        """Return the application version for a sample."""
        application_tag: str = self.get_application_tag(sample)
        return self.status_db.get_current_application_version_by_tag(application_tag)

    def create_down_sampling_working_directory(self) -> Path:
        """Create a working directory for the downsample job."""
        working_directory: Path = self.fastq_file_output_directory
        if working_directory.exists():
            raise FileExistsError(f"Working directory {working_directory} already exists.")
        LOG.info(f"Creating working directory {working_directory}")
        working_directory.mkdir(parents=True, exist_ok=True)
        return working_directory
