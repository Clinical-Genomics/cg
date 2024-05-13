"""API that handles downsampling of samples."""

import logging
from pathlib import Path

from cg.apps.demultiplex.sample_sheet.validators import validate_sample_id
from cg.exc import DownsampleFailedError
from cg.meta.meta import MetaAPI
from cg.meta.workflow.downsample.downsample import DownsampleWorkflow
from cg.models.cg_config import CGConfig
from cg.models.downsample.downsample_data import DownsampleData
from cg.store.models import Case, CaseSample, Sample
from cg.utils.calculations import multiply_by_million

LOG = logging.getLogger(__name__)


class DownsampleAPI(MetaAPI):
    def __init__(
        self,
        config: CGConfig,
        dry_run: bool = False,
    ):
        """Initialize the API."""
        super().__init__(config)
        self.dry_run: bool = dry_run

    def get_downsample_data(
        self, sample_id: str, number_of_reads: float, case_id: str, case_name: str
    ) -> DownsampleData:
        """Return the DownSampleData.
        Raises:
            DownsampleFailedError
        """
        try:
            return DownsampleData(
                status_db=self.status_db,
                hk_api=self.housekeeper_api,
                sample_id=sample_id,
                number_of_reads=number_of_reads,
                case_id=case_id,
                case_name=case_name,
                out_dir=Path(self.config.downsample.downsample_dir),
            )
        except Exception as error:
            raise DownsampleFailedError(repr(error))

    def store_downsampled_sample(self, downsample_data: DownsampleData) -> None:
        """
        Add a downsampled sample entry to StatusDB.
        Raises:
            ValueError
        """
        downsampled_sample: Sample = downsample_data.downsampled_sample
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

    def store_downsampled_case(self, downsample_data: DownsampleData) -> None:
        """
        Add a down sampled case entry to StatusDB.
        """
        downsampled_case: Case = downsample_data.downsampled_case
        if self.status_db.case_with_name_exists(case_name=downsampled_case.name):
            LOG.info(f"Case with name {downsampled_case.name} already exists in StatusDB.")
            return
        if not self.dry_run:
            self.status_db.session.add(downsampled_case)
            self.status_db.session.commit()
            LOG.info(f"New down sampled case created: {downsampled_case.internal_id}")

    def _link_downsampled_sample_to_case(
        self, downsample_data: DownsampleData, sample: Sample, case: Case
    ) -> None:
        """Create a link between sample and case in statusDB."""
        sample_case_link: CaseSample = self.status_db.relate_sample(
            case=case,
            sample=sample,
            status=downsample_data.get_sample_status(),
        )
        if self.dry_run:
            return
        self.status_db.session.add(sample_case_link)
        self.status_db.session.commit()
        LOG.info(f"Related sample {sample.internal_id} to {case.internal_id}")

    def store_downsampled_sample_case(self, downsample_data: DownsampleData) -> None:
        """
        Add the downsampled sample and case to statusDB and generate the sample case link.
        """
        self.store_downsampled_sample(downsample_data)
        self.store_downsampled_case(downsample_data)
        self._link_downsampled_sample_to_case(
            downsample_data=downsample_data,
            sample=downsample_data.downsampled_sample,
            case=downsample_data.downsampled_case,
        )

    def start_downsample_job(
        self,
        downsample_data: DownsampleData,
        account: str,
    ) -> int:
        """
        Start a down sample job for a sample.
        -Retrieves input directory from the latest version of a sample bundle in Housekeeper
        -Starts a down sample job
        """
        downsample_work_flow = DownsampleWorkflow(
            number_of_reads=multiply_by_million(downsample_data.number_of_reads),
            config=self.config,
            output_fastq_dir=str(downsample_data.fastq_file_output_directory),
            input_fastq_dir=str(downsample_data.fastq_file_input_directory),
            original_sample=downsample_data.original_sample,
            downsampled_sample=downsample_data.downsampled_sample,
            account=account,
            dry_run=self.dry_run,
        )
        return downsample_work_flow.write_and_submit_sbatch_script()

    def downsample_sample(
        self,
        sample_id: str,
        case_name: str,
        case_id: str,
        number_of_reads: float,
        account: str | None = None,
    ) -> int | None:
        """Downsample a sample."""
        LOG.info(f"Starting Downsampling for sample {sample_id}.")
        validate_sample_id(sample_id)
        downsample_data: DownsampleData = self.get_downsample_data(
            sample_id=sample_id,
            case_id=case_id,
            number_of_reads=number_of_reads,
            case_name=case_name,
        )
        if self.prepare_fastq_api.is_sample_decompression_needed(
            downsample_data.original_sample.internal_id
        ):
            self.prepare_fastq_api.compress_api.decompress_spring(
                downsample_data.original_sample.internal_id
            )
            return
        LOG.debug("No Decompression needed.")
        self.store_downsampled_sample_case(downsample_data=downsample_data)
        if not self.dry_run:
            downsample_data.create_down_sampling_working_directory()
        submitted_job: int = self.start_downsample_job(
            downsample_data=downsample_data, account=account
        )
        return submitted_job
