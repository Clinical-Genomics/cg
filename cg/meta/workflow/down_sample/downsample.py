import logging
from pathlib import Path
from typing import Optional

from cg.meta.workflow.down_sample.sbatch import WORKFLOW_TEMPLATE
from cg.models.cg_config import CGConfig

from cg.store.models import Sample
from cg.apps.slurm.slurm_api import SlurmAPI

LOG = logging.getLogger("logger")


class DownSampleWorkflow:
    def __init__(
        self,
        config: CGConfig,
        number_of_reads: int,
        down_sampled_sample: Sample,
        dry_run: bool,
        output_fastq_dir: str,
        input_fastq_dir: str,
        original_sample: Sample,
    ):
        if dry_run:
            down_sampled_sample = Sample()
            original_sample = Sample()

        self.config: CGConfig = config
        self.down_sampled_sample: Sample = down_sampled_sample
        self.number_of_reads: int = number_of_reads
        self.dry_run: bool = dry_run
        self.input_fastq_dir: str = input_fastq_dir
        self.original_sample: Sample = original_sample
        self.output_fastq_dir: str = output_fastq_dir
        self.slurm_api: SlurmAPI = SlurmAPI()
        self._account: str
        self._memory: str
        self._number_tasks: str
        self._time: str
        self._quality_of_service: str
        self._email: str

    @property
    def account(self) -> str:
        return self._account

    @account.setter
    def account(self, account: Optional[str]) -> None:
        if account:
            self._account = account
        else:
            self._account = "production"

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, email: Optional[str]) -> None:
        if email:
            self._email = email
        else:
            self._email = "karl.nyren@scilifelab.se"

    @property
    def bin_downsample(self) -> str:
        return Path("home", "proj", "production", "bin", "downsample.sh").name

    @property
    def job_name(self) -> str:
        LOG.info(
            f"Jobname: downsample_{self.original_sample.internal_id}_to_{self.down_sampled_sample.internal_id}"
        )
        return f"downsample_{self.original_sample.internal_id}_to_{self.down_sampled_sample.internal_id}"

    @property
    def memory(self) -> str:
        LOG.info(f"Memory: {self._memory}")
        return self._memory

    @memory.setter
    def memory(self, memory: Optional[str]) -> None:
        if memory:
            self._memory = memory
        else:
            self._memory = "100"

    @property
    def number_tasks(self) -> str:
        LOG.info(f"Number of tasks: {self._number_tasks}")
        return self._number_tasks

    @number_tasks.setter
    def number_tasks(self, number_tasks: str) -> None:
        if number_tasks:
            self._number_tasks = number_tasks
        else:
            self._number_tasks = "2"

    @property
    def original_sample_reads(self) -> int:
        LOG.info(f"Original sample reads: {self.original_sample.reads}")
        return self.original_sample.reads

    @property
    def quality_of_service(self) -> str:
        LOG.info(f"Submitting job with qos: {self._quality_of_service}")
        return self._quality_of_service

    @quality_of_service.setter
    def quality_of_service(self, quality_of_service: Optional[None]) -> None:
        if quality_of_service:
            self._quality_of_service = quality_of_service
        else:
            self._quality_of_service = "normal"

    @property
    def sbatch_content(self) -> str:
        return WORKFLOW_TEMPLATE.format(
            account=self.account,
            bin_downsample=self.bin_downsample,
            config_path=self.config,
            downsample_to=str(self.number_of_reads),
            bundle=self.down_sampled_sample.internal_id if not self.dry_run else "dry_run",
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
            f"{self.down_sampled_sample.internal_id}_down_sample.sh"
            if not self.dry_run
            else "dry_run_downsample.sh"
        )

    @property
    def time(self) -> str:
        LOG.info(f"Time for down sampling: {self._time}")
        return self._time

    @time.setter
    def time(self, time: Optional[str]) -> None:
        if time:
            self._time = time
        else:
            self._time = "10:00:00"

    def write_and_submit_sbatch_script(self) -> int:
        sbatch_path = Path(self.output_fastq_dir, self.sbatch_name)
        self.slurm_api.set_dry_run(dry_run=self.dry_run)

        return self.slurm_api.submit_sbatch(
            sbatch_content=self.sbatch_content,
            sbatch_path=sbatch_path,
        )
