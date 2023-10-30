"""API that handles downsampling of samples."""
import logging
from pathlib import Path
from typing import List

from cg.apps.downsample.utils import case_exists_in_statusdb, sample_exists_in_statusdb
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants import SequencingFileTag
from cg.exc import DownsampleFailedError
from cg.meta.meta import MetaAPI
from cg.meta.workflow.downsample.downsample import DownsampleWorkflow
from cg.models.cg_config import CGConfig
from cg.models.downsample.downsample_data import DownsampleData
from cg.store import Store
from cg.store.models import Family, Sample
from cg.utils.calculations import multiply_by_million
from cg.utils.files import get_files_matching_pattern

LOG = logging.getLogger(__name__)


class DownSampleAPI(MetaAPI):
    def __init__(
        self,
        config: CGConfig,
        sample_id: str,
        number_of_reads: float,
        case_id: str,
        dry_run: bool = False,
    ):
        """Initialize the API."""
        super().__init__(config)
        self.config: CGConfig = config
        self.status_db: Store = config.status_db
        self.hk_api: HousekeeperAPI = config.housekeeper_api
        self.sample_id: str = sample_id
        self.number_of_reads: float = number_of_reads
        self.case_id: str = case_id
        self.dry_run: bool = dry_run
        self.downsample_data: DownsampleData = self.get_meta_data()

    def get_meta_data(self) -> DownsampleData:
        """Return the DownSampleData.
        Raises:
            DownsampleFailedError
        """
        try:
            return DownsampleData(
                status_db=self.status_db,
                hk_api=self.housekeeper_api,
                sample_id=self.sample_id,
                number_of_reads=self.number_of_reads,
                case_id=self.case_id,
            )
        except Exception as error:
            raise DownsampleFailedError(repr(error))

    def add_downsampled_sample_entry_to_statusdb(self) -> Sample:
        """Add a down sampled sample entry to StatusDB."""
        downsampled_sample: Sample = self.downsample_data.downsampled_sample
        if sample_exists_in_statusdb(
            status_db=self.status_db, sample_id=downsampled_sample.internal_id
        ):
            raise ValueError(f"Sample {downsampled_sample.internal_id} already exists in StatusDB.")
        LOG.info(
            f"New downsampled sample created: {downsampled_sample.internal_id} from {downsampled_sample.from_sample}"
            f"Application tag set to: {downsampled_sample.application_version.application.tag}"
            f"Customer set to: {downsampled_sample.customer}"
        )
        if not self.dry_run:
            self.status_db.session.commit(downsampled_sample)
            LOG.info(f"Added {downsampled_sample.name} to StatusDB.")
            return downsampled_sample
        return downsampled_sample

    def add_downsampled_case_to_statusdb(self) -> Family:
        """
        Add a down sampled case entry to StatusDB.
        """
        downsampled_case: Family = self.downsample_data.downsampled_case
        if case_exists_in_statusdb(status_db=self.status_db, case_id=downsampled_case.internal_id):
            raise ValueError(f"Case {downsampled_case.internal_id} already exists in StatusDB.")
        if not self.dry_run:
            self.status_db.session.commit(downsampled_case)
            LOG.info(f"New down sampled case created: {downsampled_case.internal_id}")
            return downsampled_case
        return downsampled_case

    def _link_downsampled_sample_to_case(self, sample: Sample, case: Family) -> None:
        """Create a link between sample and case in statusDB."""
        if self.dry_run:
            LOG.info(f"Would relate sample {sample} to {case.internal_id}")
            return
        sample_case_link = self.status_db.relate_sample(
            family=case,
            sample=sample,
            status=self.downsample_data.sample_status(sample=sample),
        )
        self.status_db.session.commit(sample_case_link)
        LOG.info(f"Related sample {sample.internal_id} to {case.internal_id}")

    def add_downsampled_sample_case_to_statusdb(self) -> None:
        """
        Add the downsampled sample and case to statusDB and generate the sample case link.
        """
        self.add_downsampled_sample_entry_to_statusdb()
        self.add_downsampled_case_to_statusdb()
        self._link_downsampled_sample_to_case(
            sample=self.downsample_data.downsampled_sample,
            case=self.downsample_data.downsampled_case,
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
            number_of_reads=multiply_by_million(self.downsample_data.number_of_reads),
            config=self.config,
            output_fastq_dir=str(self.downsample_data.fastq_file_output_directory),
            input_fastq_dir=str(self.downsample_data.fastq_file_input_directory),
            original_sample=original_sample,
            downsampled_sample=sample_to_downsample,
            dry_run=self.dry_run,
        )
        downsample_work_flow.write_and_submit_sbatch_script()

    def add_downsampled_sample_to_housekeeper(self) -> None:
        """Add a downsampled sample to housekeeper and include the fastq files."""
        self.create_downsampled_sample_bundle()
        self.add_downsampled_fastq_files_to_housekeeper()

    def create_downsampled_sample_bundle(self) -> None:
        """Create a new bundle for the downsampled sample in housekeeper."""
        self.housekeeper_api.create_new_bundle_and_version(
            name=self.downsample_data.downsampled_sample.internal_id
        )

    def add_downsampled_fastq_files_to_housekeeper(self) -> None:
        """Add down sampled fastq files to housekeeper."""
        fastq_file_paths: List[Path] = get_files_matching_pattern(
            directory=self.downsample_data.fastq_file_output_directory,
            pattern=f"*.{SequencingFileTag.FASTQ}.gz",
        )
        for fastq_file_path in fastq_file_paths:
            self.housekeeper_api.add_and_include_file_to_latest_version(
                bundle_name=self.downsample_data.downsampled_sample.internal_id,
                file=fastq_file_path,
                tags=[SequencingFileTag.FASTQ],
            )

    def downsample_sample(self) -> None:
        """Down sample a sample."""
        if self.is_decompression_needed(self.downsample_data.downsampled_case):
            self.start_decompression(self.downsample_data.downsampled_sample)
            return
        self.add_downsampled_sample_case_to_statusdb()
        self.start_downsample_job(
            original_sample=self.downsample_data.original_sample,
            sample_to_downsample=self.downsample_data.downsampled_sample,
        )
