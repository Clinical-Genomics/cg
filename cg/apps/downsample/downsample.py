"""API that handles downsampling of samples."""
import logging
from pathlib import Path

from cg.constants import SequencingFileTag
from cg.exc import DownsampleFailedError
from cg.meta.meta import MetaAPI
from cg.meta.workflow.downsample.downsample import DownsampleWorkflow
from cg.models.cg_config import CGConfig
from cg.models.downsample.downsample_data import DownsampleData
from cg.store.models import Family, FamilySample, Sample
from cg.utils.calculations import multiply_by_million

LOG = logging.getLogger(__name__)


class DownsampleAPI(MetaAPI):
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
        self.sample_id: str = sample_id
        self.number_of_reads: float = number_of_reads
        self.case_id: str = case_id
        self.dry_run: bool = dry_run
        self.downsample_data: DownsampleData = self.get_meta_data()
        LOG.info(f"Starting DownsampleAPI for sample {sample_id}.")

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
                out_dir=Path(self.config.downsample_dir),
            )
        except Exception as error:
            raise DownsampleFailedError(repr(error))

    def store_downsampled_sample(self) -> Sample:
        """Add a down sampled sample entry to StatusDB."""
        downsampled_sample: Sample = self.downsample_data.downsampled_sample
        if self.status_db.sample_with_id_exists(sample_id=downsampled_sample.internal_id):
            raise ValueError(f"Sample {downsampled_sample.internal_id} already exists in StatusDB.")
        LOG.info(
            f"New downsampled sample created: {downsampled_sample.internal_id} from {downsampled_sample.from_sample}"
            f"Application tag set to: {downsampled_sample.application_version.application.tag}"
            f"Customer set to: {downsampled_sample.customer}"
        )
        if not self.dry_run:
            self.status_db.session.add(downsampled_sample)
            self.status_db.session.commit()
            LOG.info(f"Added {downsampled_sample.name} to StatusDB.")
            return downsampled_sample
        return downsampled_sample

    def store_downsampled_case(self) -> Family | None:
        """
        Add a down sampled case entry to StatusDB.
        """
        downsampled_case: Family = self.downsample_data.downsampled_case
        if self.status_db.case_with_name_exists(case_name=downsampled_case.name):
            LOG.info(f"Case with name {downsampled_case.name} already exists in StatusDB.")
            return
        if not self.dry_run:
            self.status_db.session.add(downsampled_case)
            self.status_db.session.commit()
            LOG.info(f"New down sampled case created: {downsampled_case.internal_id}")
            return downsampled_case
        return downsampled_case

    def _link_downsampled_sample_to_case(self, sample: Sample, case: Family) -> None:
        """Create a link between sample and case in statusDB."""
        if self.dry_run:
            LOG.info(
                f"Would relate sample {sample} to case {case.internal_id} with name {case.name}"
            )
            return
        sample_case_link: FamilySample = self.status_db.relate_sample(
            family=case,
            sample=sample,
            status=self.downsample_data.sample_status(sample=sample),
        )
        self.status_db.session.add(sample_case_link)
        self.status_db.session.commit()
        LOG.info(f"Related sample {sample.internal_id} to {case.internal_id}")

    def add_downsampled_sample_case_to_statusdb(self) -> None:
        """
        Add the downsampled sample and case to statusDB and generate the sample case link.
        """
        self.store_downsampled_sample()
        self.store_downsampled_case()
        self._link_downsampled_sample_to_case(
            sample=self.downsample_data.downsampled_sample,
            case=self.downsample_data.downsampled_case,
        )

    def is_decompression_needed(self) -> bool:
        """Check if decompression is needed for the specified case.
        Decompression is needed if there are no files with fastq tag found for the sample in housekeeper.
        """
        LOG.debug("Checking if decompression is needed.")
        is_decompression_needed: bool = False
        if not self.housekeeper_api.get_files(
            bundle=self.downsample_data.original_sample.internal_id,
            tags=[SequencingFileTag.FASTQ],
        ):
            is_decompression_needed = True
        return is_decompression_needed

    def start_decompression(self, sample: Sample) -> None:
        """Start decompression of spring compressed fastq files for the given sample."""
        LOG.info(f"Decompression for {sample.internal_id} is needed.")
        self.prepare_fastq_api.compress_api.decompress_spring(sample.internal_id)
        LOG.info("Re-run down sample command when decompression is done.")

    def start_downsample_job(self, original_sample: Sample, sample_to_downsample: Sample) -> int:
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
        return downsample_work_flow.write_and_submit_sbatch_script()

    def downsample_sample(self) -> int | None:
        """Down sample a sample."""
        if self.is_decompression_needed():
            self.start_decompression(self.downsample_data.original_sample)
            return
        LOG.debug("No Decompression needed.")
        self.add_downsampled_sample_case_to_statusdb()
        self.downsample_data.create_down_sampling_working_directory()
        submitted_job: int = self.start_downsample_job(
            original_sample=self.downsample_data.original_sample,
            sample_to_downsample=self.downsample_data.downsampled_sample,
        )
        LOG.info(f"Downsample job started with id {submitted_job}.")
        return submitted_job
