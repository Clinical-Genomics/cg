"""
Module for interacting with crunchy to perform:
    1. Compressing: FASTQ to SPRING
    2. Decompressing: SPRING to FASTQ
along with the helper methods.
"""

import logging
from pathlib import Path

from cg.apps.crunchy import files
from cg.apps.crunchy.models import CrunchyFile, CrunchyMetadata
from cg.apps.crunchy.sbatch import (
    FASTQ_TO_SPRING_COMMANDS,
    FASTQ_TO_SPRING_ERROR,
    SPRING_TO_FASTQ_COMMANDS,
    SPRING_TO_FASTQ_ERROR,
)
from cg.apps.slurm.slurm_api import SlurmAPI
from cg.constants.priority import SlurmQos
from cg.models.compression_data import CompressionData
from cg.models.slurm.sbatch import Sbatch

LOG = logging.getLogger(__name__)


class CrunchyAPI:
    """
    API for Crunchy.
    """

    def __init__(self, config: dict):
        self.conda_binary: str | None = config["crunchy"]["conda_binary"] or None
        self.crunchy_env: str = config["crunchy"]["slurm"]["conda_env"]
        self.dry_run: bool = False
        self.reference_path: str = config["crunchy"]["cram_reference"]
        self.slurm_api: SlurmAPI = SlurmAPI()
        self.slurm_account: str = config["crunchy"]["slurm"]["account"]
        self.slurm_mail_user: str = config["crunchy"]["slurm"]["mail_user"]
        self.slurm_number_tasks: int = config["crunchy"]["slurm"]["number_tasks"]
        self.slurm_cpus_per_task: int = config["crunchy"]["slurm"].get("cpus_per_task")
        self.slurm_partition: str = config["crunchy"]["slurm"]["partition"]
        self.tmp_dir_base: str = config["crunchy"]["tmp_dir_base"]
        # Used only when a job's memory/time can't be scaled from its read count.
        self.fallback_memory: int = config["crunchy"]["fallback_memory"]
        self.fallback_minutes: int = config["crunchy"]["fallback_minutes"]

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run."""
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    @staticmethod
    def create_pending_file(pending_path: Path, dry_run: bool) -> None:
        """Create a pending flag file."""
        LOG.info(f"Creating pending flag {pending_path}")
        if dry_run:
            return
        pending_path.touch(exist_ok=False)

    # These are the compression/decompression methods
    def fastq_to_spring(
        self, compression_obj: CompressionData, memory: int, minutes: int, sample_id: str = ""
    ) -> int:
        """Compress FASTQ files into SPRING by sending to sbatch SLURM."""
        CrunchyAPI.create_pending_file(
            pending_path=compression_obj.pending_path, dry_run=self.dry_run
        )
        log_dir: Path = files.get_log_dir(compression_obj.spring_path)
        # Generate the error function
        error_function = FASTQ_TO_SPRING_ERROR.format(
            spring_path=compression_obj.spring_path, pending_path=compression_obj.pending_path
        )
        # Generate the commands
        sbatch_parameters: Sbatch
        commands = FASTQ_TO_SPRING_COMMANDS.format(
            conda_run=f"{self.conda_binary} run --no-capture-output --name {self.crunchy_env}",
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            pending_path=compression_obj.pending_path,
            spring_path=compression_obj.spring_path,
            threads=self.slurm_number_tasks,
            tmp_dir=files.get_tmp_dir(base=self.tmp_dir_base),
        )
        sbatch_parameters: Sbatch = Sbatch(
            account=self.slurm_account,
            commands=commands,
            email=self.slurm_mail_user,
            error=error_function,
            hours=minutes // 60,
            minutes=f"{minutes % 60:02d}",
            job_name="_".join([sample_id, compression_obj.run_name, "fastq_to_spring"]),
            log_dir=log_dir.as_posix(),
            memory=memory,
            number_tasks=self.slurm_number_tasks,
            quality_of_service=SlurmQos.MAINTENANCE,
            partition=f"--partition={self.slurm_partition}",
            chdir=f"--chdir={self.tmp_dir_base}",
            cpus_per_task=f"--cpus-per-task={self.slurm_cpus_per_task}",
        )
        sbatch_content: str = self.slurm_api.generate_sbatch_content(
            sbatch_parameters=sbatch_parameters
        )
        sbatch_path: Path = files.get_fastq_to_spring_sbatch_path(
            log_dir=log_dir, run_name=compression_obj.run_name
        )
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info(f"Fastq compression running as job {sbatch_number}")
        return sbatch_number

    def spring_to_fastq(
        self, compression_obj: CompressionData, memory: int, minutes: int, sample_id: str = ""
    ) -> int:
        """Decompress SPRING into FASTQ by submitting sbatch script to SLURM."""
        CrunchyAPI.create_pending_file(
            pending_path=compression_obj.pending_path, dry_run=self.dry_run
        )
        # Fetch the metadata information from a spring metadata file
        crunchy_metadata: CrunchyMetadata = files.get_crunchy_metadata(
            compression_obj.spring_metadata_path
        )
        files_info: dict[str, CrunchyFile] = files.get_spring_archive_files(crunchy_metadata)
        log_dir = files.get_log_dir(compression_obj.spring_path)

        error_function = SPRING_TO_FASTQ_ERROR.format(
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            pending_path=compression_obj.pending_path,
        )
        commands = SPRING_TO_FASTQ_COMMANDS.format(
            conda_run=f"{self.conda_binary} run --no-capture-output --name {self.crunchy_env}",
            tmp_dir=files.get_tmp_dir(base=self.tmp_dir_base),
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            spring_path=compression_obj.spring_path,
            pending_path=compression_obj.pending_path,
            threads=self.slurm_number_tasks,
            checksum_first=files_info["fastq_first"].checksum,
            checksum_second=files_info["fastq_second"].checksum,
        )
        sbatch_parameters: Sbatch = Sbatch(
            account=self.slurm_account,
            commands=commands,
            email=self.slurm_mail_user,
            error=error_function,
            hours=minutes // 60,
            minutes=f"{minutes % 60:02d}",
            job_name="_".join([sample_id, compression_obj.run_name, "spring_to_fastq"]),
            log_dir=log_dir.as_posix(),
            memory=memory,
            number_tasks=self.slurm_number_tasks,
            quality_of_service=SlurmQos.HIGH,
            partition=f"--partition={self.slurm_partition}",
            chdir=f"--chdir={self.tmp_dir_base}",
            cpus_per_task=f"--cpus-per-task={self.slurm_cpus_per_task}",
        )
        sbatch_content: str = self.slurm_api.generate_sbatch_content(sbatch_parameters)
        sbatch_path = files.get_spring_to_fastq_sbatch_path(
            log_dir=log_dir, run_name=compression_obj.run_name
        )
        sbatch_number: int = self.slurm_api.submit_sbatch(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path
        )
        LOG.info(f"Spring decompression running as job {sbatch_number}")
        return sbatch_number
