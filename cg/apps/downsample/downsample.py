"""API that handles downsampling of samples."""
import logging
from pathlib import Path
from typing import List

from cg.constants import Priority, SequencingFileTag
from cg.meta.meta import MetaAPI
from cg.meta.workflow.downsample.downsample import DownsampleWorkflow
from cg.models.cg_config import CGConfig
from cg.store.models import ApplicationVersion, Family, Sample
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


class DownsampleMetaData:
    def __init__(
        self, config: CGConfig, sample_internal_id: str, number_of_reads: int, case_internal_id: str
    ):
        """Initialize the model."""
        self.config = config
        self.sample_internal_id: str = sample_internal_id
        self.number_of_reads: int = number_of_reads
        self.case_internal_id: str = case_internal_id
        self.original_sample: Sample = self.get_sample_to_downsample()
        self.original_case: Family = self.get_case_to_downsample()
        self.has_enough_reads: bool = self.has_enough_reads_to_downsample()
        self.downsampled_sample: Sample = self._generate_statusdb_downsampled_sample_record()
        self.downsampled_case: Family = self._generate_statusdb_downsampled_case()
        self.create_down_sampling_working_directory()
        LOG.info(f"Pre-flight checks completed for {self.sample_internal_id}")

    def multiply_reads_by_million(
        self,
    ) -> int:
        """Multiply the given number of reads by a million."""
        return self.number_of_reads * 1_000_000

    @property
    def downsampled_sample_name(
        self,
    ) -> str:
        """Return a new sample name with the number of reads to which it is down sampled in millions appended."""
        new_name: str = f"{self.sample_internal_id}_{self.number_of_reads}M"
        LOG.info(f"Changed {self.sample_internal_id} to {new_name}")
        return new_name

    @property
    def downsampled_case_name(
        self,
    ) -> str:
        """Return a case name with _DS appended."""
        new_name: str = f"{self.case_internal_id}DS"
        LOG.info(f"Changed {self.case_internal_id} to {new_name}")
        return new_name

    def get_sample_to_downsample(self) -> Sample:
        """Check if a sample exists in StatusDB."""
        sample: Sample = self.config.status_db.get_sample_by_internal_id(self.sample_internal_id)
        if not sample:
            raise ValueError(f"Sample {self.sample_internal_id} not found in StatusDB.")
        return sample

    def get_case_to_downsample(self) -> Family:
        """Check if a case exists in StatusDB."""
        case: Family = self.config.status_db.get_case_by_internal_id(self.case_internal_id)
        if not case:
            raise ValueError(f"Case {self.case_internal_id} not found in StatusDB.")
        return case

    def _generate_statusdb_downsampled_sample_record(
        self,
    ) -> Sample:
        """
        Generate a down sampled sample record for StatusDB.
        The new sample contains the original sample internal id and meta data.
        """
        application_version: ApplicationVersion = self.get_application_version(self.original_sample)
        downsampled_sample: Sample = self.config.status_db.add_sample(
            name=self.downsampled_sample_name,
            internal_id=self.downsampled_sample_name,
            sex=self.original_sample.sex,
            order=self.original_sample.order,
            downsampled_to=self.multiply_reads_by_million(),
            from_sample=self.original_sample.internal_id,
            tumour=self.original_sample.is_tumour,
            priority=Priority.standard,
            customer=self.original_sample.customer,
            application_version=application_version,
        )
        if self.sample_exists_in_statusdb(downsampled_sample.internal_id):
            raise ValueError(f"Sample {downsampled_sample.internal_id} already exists in StatusDB.")
        return downsampled_sample

    def _generate_statusdb_downsampled_case(
        self,
    ) -> Family:
        """Generate a case for the down sampled samples. The new case uses existing case data."""
        downsampled_case: Family = self.config.status_db.add_case(
            data_analysis=self.original_case.data_analysis,
            data_delivery=self.original_case.data_delivery,
            name=self.downsampled_case_name,
            panels=["OMIM-AUTO"],
            priority=self.original_case.priority,
            ticket=self.original_case.latest_ticket,
        )
        downsampled_case.customer = self.original_case.customer
        if self.case_exists_in_statusdb(downsampled_case.internal_id):
            raise ValueError(f"Case {downsampled_case.internal_id} already exists in StatusDB.")
        return downsampled_case

    def case_exists_in_statusdb(self, case_internal_id: str) -> bool:
        """Check if a case exists in StatusDB."""
        case: Family = self.config.status_db.get_case_by_internal_id(case_internal_id)
        if case:
            return True
        return False

    def sample_exists_in_statusdb(self, sample_internal_id: str) -> bool:
        """Check if a sample exists in StatusDB."""
        sample: Sample = self.config.status_db.get_sample_by_internal_id(sample_internal_id)
        if sample:
            return True
        return False

    def has_enough_reads_to_downsample(self) -> bool:
        """Check if the sample has enough reads to down sample."""
        if not self.original_sample.reads > self.number_of_reads * 1_000_000:
            raise ValueError(
                f"Sample {self.original_sample.internal_id} does not have enough reads ({self.original_sample.reads}) to down sample to "
                f"{self.number_of_reads}M."
            )
        return True

    @property
    def fastq_file_input_directory(self) -> Path:
        """Get the latest version directory for a sample in housekeeper."""
        return Path(
            self.config.housekeeper_api.get_file_from_latest_version(
                bundle_name=self.original_sample.internal_id, tags={SequencingFileTag.FASTQ}
            ).path
        ).parent

    @property
    def fastq_file_output_directory(self):
        """Get the output directory for the down sampled sample."""
        return Path("home", "proj", "production", "downsample", self.downsampled_sample.internal_id)

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
        return self.config.status_db.get_current_application_version_by_tag(application_tag)

    def create_down_sampling_working_directory(self) -> Path:
        """Create a working directory for the down sample job."""
        working_directory: Path = self.fastq_file_output_directory
        if working_directory.exists():
            raise FileExistsError(f"Working directory {working_directory} already exists.")
        LOG.info(f"Creating working directory {working_directory}")
        working_directory.mkdir(parents=True, exist_ok=True)
        return working_directory


class DownSampleAPI(MetaAPI):
    def __init__(
        self, config: CGConfig, sample_reads: str, case_internal_id: str, dry_run: bool = False
    ):
        """Initialize the API."""
        super().__init__(config)
        self.config = config
        self.sample_reads: str = sample_reads
        self.case_internal_id: str = case_internal_id
        self.dry_run: bool = dry_run
        self.downsample_meta_data: DownsampleMetaData = self.get_meta_data()

    @staticmethod
    def parse_sample_reads_input(
        sample_reads: str, case_internal_id: str, config: CGConfig
    ) -> DownsampleMetaData:
        """Parse the sample reads input into the SampleToDownSample model."""
        sample_internal_id: str
        number_of_reads: int
        sample_internal_id, number_of_reads = sample_reads.split(";")
        return DownsampleMetaData(
            config=config,
            sample_internal_id=sample_internal_id,
            number_of_reads=number_of_reads,
            case_internal_id=case_internal_id,
        )

    def get_meta_data(self) -> DownsampleMetaData:
        return self.parse_sample_reads_input(
            sample_reads=self.sample_reads,
            case_internal_id=self.case_internal_id,
            config=self.config,
        )

    def add_downsampled_sample_entry_to_statusdb(self) -> Sample:
        """Add a down sampled sample entry to StatusDB."""
        downsampled_sample: Sample = self.downsample_meta_data.downsampled_sample
        LOG.info(
            f"New downsampled sample created: {downsampled_sample.internal_id} from {downsampled_sample.from_sample}"
            f"Application tag set to: {downsampled_sample.application_version.application.tag}"
            f"Customer set to: {downsampled_sample.customer}"
        )
        if not self.dry_run:
            self.status_db.session.add_commit(downsampled_sample)
            LOG.info(f"Added {downsampled_sample.name} to StatusDB.")
            return downsampled_sample
        return downsampled_sample

    def add_downsampled_case_to_statusdb(self) -> Family:
        """
        Add a down sampled case entry to StatusDB.
        Checks if the down sampled case already exists in StatusDB.
        """
        downsampled_case: Family = self.downsample_meta_data.downsampled_case
        if not self.dry_run:
            self.status_db.session.add_commit(downsampled_case)
            LOG.info(f"New down sampled case created: {downsampled_case.name}")
            return downsampled_case
        LOG.info(f"Case {downsampled_case.internal_id} already exists in StatusDB.")
        return downsampled_case

    def _link_downsampled_sample_to_case(self, sample: Sample, case: Family) -> None:
        """Create a link between sample and case in statusDB."""
        if self.dry_run:
            LOG.info(f"Would relate sample {sample} to {case.internal_id}")
            return
        sample_case_link = self.status_db.relate_sample(
            family=case,
            sample=sample,
            status=self.downsample_meta_data.sample_status(sample=sample),
        )
        self.status_db.session.add_commit(sample_case_link)
        LOG.info(f"Related sample {sample.internal_id} to {case.internal_id}")

    def add_downsampled_sample_case_to_statusdb(self) -> None:
        """
        Add the down sampled sample and case to statusDB and generate the sample case link.
            -Asserts that both the original sample and case exists in statusDB.
            -Asserts that the down sampled sample and case does not already exist in statusDB.
            -Asserts that the original sample has more reads than the number to which it is down sampled.
        """
        self.add_downsampled_sample_entry_to_statusdb()
        self.add_downsampled_case_to_statusdb()
        self._link_downsampled_sample_to_case(
            sample=self.downsample_meta_data.downsampled_sample,
            case=self.downsample_meta_data.downsampled_case,
        )

    def is_decompression_needed(self, case) -> bool:
        """Check if decompression is needed for the specified case."""
        return self.prepare_fastq_api.is_spring_decompression_needed(case.internal_id)

    def start_decompression(self, sample: Sample) -> None:
        """Start decompression of spring compressed fastq files for the given sample."""
        LOG.info(f"Decompression for {sample.internal_id} is needed.")
        self.prepare_fastq_api.compress_api.decompress_spring(sample.internal_id)
        LOG.info("Re-run down sample command when decompression is done.")

    def start_downsample_job(self, original_sample: Sample, sample_to_downsample: Sample) -> None:
        """
        Start a down sample job for a sample.
        -Retrieves input directory from the latest version of a sample bundle in housekeeper
        -Starts a down sample job
        """
        downsample_work_flow = DownsampleWorkflow(
            number_of_reads=self.downsample_meta_data.multiply_reads_by_million(),
            config=self.config,
            output_fastq_dir=str(self.downsample_meta_data.fastq_file_output_directory),
            input_fastq_dir=str(self.downsample_meta_data.fastq_file_input_directory),
            original_sample=original_sample,
            downsampled_sample=sample_to_downsample,
            dry_run=self.dry_run,
        )
        downsample_work_flow.write_and_submit_sbatch_script()

    def add_downsampled_sample_to_housekeeper(self) -> None:
        """Add a down sampled sample to housekeeper and include the fastq files."""
        self.create_downsampled_sample_bundle()
        self.add_downsampled_fastq_files_to_housekeeper()

    def create_downsampled_sample_bundle(self) -> None:
        """Create a new bundle for the down sampled sample in housekeeper."""
        self.config.housekeeper_api.create_new_bundle_and_version(
            name=self.downsample_meta_data.downsampled_sample.internal_id
        )

    def add_downsampled_fastq_files_to_housekeeper(self) -> None:
        """Add down sampled fastq files to housekeeper."""
        fastq_file_paths: List[Path] = get_files_matching_pattern(
            directory=self.downsample_meta_data.fastq_file_output_directory,
            pattern=f"*.{SequencingFileTag.FASTQ}",
        )
        for fastq_file_path in fastq_file_paths:
            self.housekeeper_api.add_and_include_file_to_latest_version(
                bundle_name=self.downsample_meta_data.downsampled_sample.internal_id,
                file=fastq_file_path,
                tags=[SequencingFileTag.FASTQ],
            )

    def downsample_sample(self) -> None:
        """Down sample a sample."""
        if self.is_decompression_needed(self.downsample_meta_data.downsampled_case):
            self.start_decompression(self.downsample_meta_data.downsampled_sample)
            return
        self.add_downsampled_sample_case_to_statusdb()
        self.add_downsampled_sample_to_housekeeper()
        self.start_downsample_job(
            original_sample=self.downsample_meta_data.original_sample,
            sample_to_downsample=self.downsample_meta_data.downsampled_sample,
        )
