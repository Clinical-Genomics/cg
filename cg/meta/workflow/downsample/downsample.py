import logging
from pathlib import Path

from cg.apps.slurm.slurm_api import SlurmAPI
from cg.meta.workflow.downsample.sbatch import WORKFLOW_TEMPLATE
from cg.models.cg_config import CGConfig
from cg.store.models import Sample

LOG = logging.getLogger("logger")


class DownsampleWorkflow:
    def __init__(
        self,
        config: CGConfig,
        number_of_reads: int,
        downsampled_sample: Sample,
        dry_run: bool,
        output_fastq_dir: str,
        input_fastq_dir: str,
        original_sample: Sample,
        account: str = None,
    ):
        if dry_run:
            downsampled_sample = Sample()
            original_sample = Sample()

        self.config: CGConfig = config
        self.downsampled_sample: Sample = downsampled_sample
        self.number_of_reads: int = number_of_reads
        self.dry_run: bool = dry_run
        self.input_fastq_dir: str = input_fastq_dir
        self.original_sample: Sample = original_sample
        self.output_fastq_dir: str = output_fastq_dir
        self.slurm_api: SlurmAPI = SlurmAPI()
        self._account: str = account or self.config.downsample.account
        self._memory: str = "100"
        self._number_tasks: str = "2"
        self._time: str = "10:00:00"
        self._quality_of_service: str = "normal"
        self._email: str = "hiseq.clinical@scilifelab.se"

    @property
    def account(self) -> str:
        return self._account

    @property
    def email(self) -> str:
        return self._email

    @property
    def downsample_script_path(self) -> str:
        """The path to the downsample.sh script on Hasta."""
        return self.config.downsample.downsample_script

    @property
    def job_name(self) -> str:
        LOG.info(
            f"Jobname: downsample_{self.original_sample.internal_id}_to_{self.downsampled_sample.internal_id}"
        )
        return f"downsample_{self.original_sample.internal_id}_to_{self.downsampled_sample.internal_id}"

    @property
    def memory(self) -> str:
        LOG.info(f"Memory: {self._memory}")
        return self._memory

    @property
    def number_tasks(self) -> str:
        LOG.info(f"Number of tasks: {self._number_tasks}")
        return self._number_tasks

    @property
    def original_sample_reads(self) -> int:
        LOG.info(f"Original sample reads: {self.original_sample.reads}")
        return self.original_sample.reads

    @property
    def quality_of_service(self) -> str:
        LOG.info(f"Submitting job with qos: {self._quality_of_service}")
        return self._quality_of_service

    @property
    def sbatch_content(self) -> str:
        return WORKFLOW_TEMPLATE.format(
            account=self.account,
            bin_downsample=self.downsample_script_path,
            config_path=self.config,
            downsample_to=str(self.number_of_reads),
            bundle=self.downsampled_sample.internal_id if not self.dry_run else "dry_run",
            email=self.email,
            input_fastq_dir=self.input_fastq_dir,
            job_name=self.job_name,
            memory=self.memory,
            number_tasks=self.number_tasks,
            original_sample_reads=self.original_sample_reads,
            output_fastq_dir=self.output_fastq_dir,
            quality_of_service=self.quality_of_service,
            time=self.time,
        )

    @property
    def sbatch_name(self) -> str:
        return (
            f"{self.downsampled_sample.internal_id}_downsample.sh"
            if not self.dry_run
            else "dry_run_downsample.sh"
        )

    @property
    def time(self) -> str:
        LOG.info(f"Time for down sampling: {self._time}")
        return self._time

    def write_and_submit_sbatch_script(self) -> int:
        sbatch_path = Path(self.output_fastq_dir, self.sbatch_name)
        self.slurm_api.set_dry_run(dry_run=self.dry_run)

        return self.slurm_api.submit_sbatch(
            sbatch_content=self.sbatch_content,
            sbatch_path=sbatch_path,
        )
