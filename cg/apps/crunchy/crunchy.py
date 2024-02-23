"""
    Module for interacting with crunchy to perform:
        1. Compressing: FASTQ to SPRING
        2. Decompressing: SPRING to FASTQ
    along with the helper methods.
"""

import datetime
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
from cg.constants import FASTQ_DELTA
from cg.constants.priority import SlurmQos
from cg.models import CompressionData
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
        self.slurm_hours: int = config["crunchy"]["slurm"]["hours"]
        self.slurm_mail_user: str = config["crunchy"]["slurm"]["mail_user"]
        self.slurm_memory: int = config["crunchy"]["slurm"]["memory"]
        self.slurm_number_tasks: int = config["crunchy"]["slurm"]["number_tasks"]

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run."""
        LOG.info("Updating compress api")
        LOG.info(f"Set dry run to {dry_run}")
        self.dry_run = dry_run
        self.slurm_api.set_dry_run(dry_run=dry_run)

    # Methods to check compression status
    @staticmethod
    def is_compression_pending(compression_obj: CompressionData) -> bool:
        """Check if compression/decompression has started but not finished."""
        if compression_obj.pending_exists():
            LOG.info(f"Compression/decompression is pending for {compression_obj.run_name}")
            return True
        LOG.info("Compression/decompression is not running")
        return False

    @staticmethod
    def is_fastq_compression_possible(compression_obj: CompressionData) -> bool:
        """Check if FASTQ compression is possible.

        - Compression is running          -> Compression NOT possible
        - SPRING file exists on Hasta     -> Compression NOT possible
        - Data is external                -> Compression NOT possible
        - Not compressed and
           not running  -> Compression IS possible
        """
        if CrunchyAPI.is_compression_pending(compression_obj):
            return False

        if compression_obj.spring_exists():
            LOG.debug("SPRING file found")
            return False

        if "external-data" in str(compression_obj.fastq_first):
            LOG.debug("File is external data and should not be compressed")
            return False

        LOG.debug("FASTQ compression is possible")

        return True

    @staticmethod
    def is_spring_decompression_possible(compression_obj: CompressionData) -> bool:
        """Check if SPRING decompression is possible.

        There are three possible answers to this question:

            - Compression/Decompression is running      -> Decompression is NOT possible
            - The FASTQ files are not compressed        -> Decompression is NOT possible
            - Compression has been performed            -> Decompression IS possible

        """
        if compression_obj.pending_exists():
            LOG.info(f"Compression/decompression is pending for {compression_obj.run_name}")
            return False

        if not compression_obj.spring_exists():
            LOG.info("No SPRING file found")
            return False

        if compression_obj.pair_exists():
            LOG.info("FASTQ files already exists")
            return False

        LOG.info("Decompression is possible")

        return True

    @staticmethod
    def is_fastq_compression_done(compression: CompressionData) -> bool:
        """Check if FASTQ compression is finished.

        This is checked by controlling that the SPRING files that are produced after FASTQ
        compression exists.

        The following has to be fulfilled for FASTQ compression to be considered done:

            - A SPRING archive file exists
            - A SPRING archive metadata file exists
            - The SPRING archive has not been unpacked before FASTQ delta (21 days)

        Note:
        'updated_at' indicates at what date the SPRING archive was unarchived last.
        If the SPRING archive has never been unarchived 'updated_at' is None.

        """
        LOG.info("Check if FASTQ compression is finished")
        LOG.info(f"Check if SPRING file {compression.spring_path} exists")
        if not compression.spring_exists():
            LOG.info(
                f"No SPRING file for {compression.run_name}",
            )
            return False
        LOG.info("SPRING file found")

        LOG.info(f"Check if SPRING metadata file {compression.spring_metadata_path} exists")
        if not compression.metadata_exists():
            LOG.info("No metadata file found")
            return False
        LOG.info("SPRING metadata file found")

        # We want this to raise exception if file is malformed
        crunchy_metadata: CrunchyMetadata = files.get_crunchy_metadata(
            compression.spring_metadata_path
        )

        # Check if the SPRING archive has been unarchived
        updated_at: datetime.date | None = files.get_file_updated_at(crunchy_metadata)
        if updated_at is None:
            LOG.info(f"FASTQ compression is done for {compression.run_name}")
            return True

        LOG.info(f"Files where unpacked {updated_at}")

        if not CrunchyAPI.check_if_update_spring(updated_at):
            return False

        LOG.info(f"FASTQ compression is done for {compression.run_name}")

        return True

    @staticmethod
    def is_spring_decompression_done(compression_obj: CompressionData) -> bool:
        """Check if SPRING decompression if finished.

        This means that all three files specified in SPRING metadata should exist.
        That is

            - First read in FASTQ pair should exist
            - Second read in FASTQ pair should exist
            - SPRING archive file should still exist
        """

        spring_metadata_path: Path = compression_obj.spring_metadata_path
        LOG.info(f"Check if SPRING metadata file {spring_metadata_path} exists")

        if not compression_obj.metadata_exists():
            LOG.info("No SPRING metadata file found")
            return False

        # We want this to exit hard if the metadata is malformed
        crunchy_metadata: CrunchyMetadata = files.get_crunchy_metadata(spring_metadata_path)

        for file_info in crunchy_metadata.files:
            if not Path(file_info.path).exists():
                LOG.info(f"File {file_info.path} does not exist")
                return False
            if not file_info.updated:
                LOG.info("Files have not been unarchived")
                return False

        LOG.info(f"SPRING decompression is done for run {compression_obj.run_name}")
        return True

    @staticmethod
    def create_pending_file(pending_path: Path, dry_run: bool) -> None:
        """Create a pending flag file."""
        LOG.info(f"Creating pending flag {pending_path}")
        if dry_run:
            return
        pending_path.touch(exist_ok=False)

    # These are the compression/decompression methods
    def fastq_to_spring(self, compression_obj: CompressionData, sample_id: str = "") -> int:
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
            conda_run=f"{self.conda_binary} run --name {self.crunchy_env}",
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            pending_path=compression_obj.pending_path,
            spring_path=compression_obj.spring_path,
            tmp_dir=files.get_tmp_dir(
                prefix="spring_",
                suffix="_compress",
                base=compression_obj.analysis_dir.as_posix(),
            ),
        )
        sbatch_parameters: Sbatch = Sbatch(
            account=self.slurm_account,
            commands=commands,
            email=self.slurm_mail_user,
            error=error_function,
            hours=self.slurm_hours,
            job_name="_".join([sample_id, compression_obj.run_name, "fastq_to_spring"]),
            log_dir=log_dir.as_posix(),
            memory=self.slurm_memory,
            number_tasks=self.slurm_number_tasks,
            quality_of_service=SlurmQos.MAINTENANCE,
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

    def spring_to_fastq(self, compression_obj: CompressionData, sample_id: str = "") -> int:
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
            conda_run=f"{self.conda_binary} run --name {self.crunchy_env}",
            tmp_dir=files.get_tmp_dir(
                prefix="spring_",
                suffix="_decompress",
                base=compression_obj.analysis_dir.as_posix(),
            ),
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            spring_path=compression_obj.spring_path,
            pending_path=compression_obj.pending_path,
            checksum_first=files_info["fastq_first"].checksum,
            checksum_second=files_info["fastq_second"].checksum,
        )
        sbatch_parameters: Sbatch = Sbatch(
            account=self.slurm_account,
            commands=commands,
            email=self.slurm_mail_user,
            error=error_function,
            hours=self.slurm_hours,
            job_name="_".join([sample_id, compression_obj.run_name, "spring_to_fastq"]),
            log_dir=log_dir.as_posix(),
            memory=self.slurm_memory,
            number_tasks=self.slurm_number_tasks,
            quality_of_service=SlurmQos.LOW,
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

    @staticmethod
    def check_if_update_spring(file_date: datetime.date) -> bool:
        """Check if date is older than FASTQ_DELTA."""
        delta = file_date + datetime.timedelta(days=FASTQ_DELTA)
        now = datetime.datetime.now()
        if delta > now.date():
            LOG.info("FASTQ files are not old enough")
            return False
        return True
