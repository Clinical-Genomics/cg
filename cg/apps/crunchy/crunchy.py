"""
    Module for interacting with crunchy to perform:
        1. Compressing: FASTQ to SPRING
        2. Decompressing: SPRING to FASTQ
    along with the helper methods
"""

import datetime
import logging
import tempfile
from pathlib import Path
from typing import Dict, Optional

from cg.constants import FASTQ_DELTA
from cg.models import CompressionData
from cg.utils import Process
from cgmodels.crunchy.metadata import CrunchyFile, CrunchyMetadata

from .files import get_crunchy_metadata, get_file_updated_at, get_spring_archive_files
from .sbatch import SBATCH_FASTQ_TO_SPRING, SBATCH_HEADER_TEMPLATE, SBATCH_SPRING_TO_FASTQ

LOG = logging.getLogger(__name__)


FLAG_PATH_SUFFIX = ".crunchy.txt"
PENDING_PATH_SUFFIX = ".crunchy.pending.txt"


class CrunchyAPI:
    """
    API for crunchy
    """

    def __init__(self, config: dict):

        self.process = Process("sbatch")
        self.slurm_account = config["crunchy"]["slurm"]["account"]
        self.crunchy_env = config["crunchy"]["slurm"]["conda_env"]
        self.mail_user = config["crunchy"]["slurm"]["mail_user"]
        self.reference_path = config["crunchy"]["cram_reference"]
        self.dry_run = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Update dry run"""
        LOG.info("Updating compress api")
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    # Methods to check compression status
    @staticmethod
    def is_compression_pending(compression_obj: CompressionData) -> bool:
        """Check if compression/decompression has started but not finished"""
        if compression_obj.pending_exists():
            LOG.info("Compression/decompression is pending for %s", compression_obj.run_name)
            return True
        LOG.info("Compression/decompression is not running")
        return False

    @staticmethod
    def is_fastq_compression_possible(compression_obj: CompressionData) -> bool:
        """Check if FASTQ compression is possible

        There are three possible answers to this question:

         - Compression is running          -> Compression NOT possible
         - SPRING archive exists           -> Compression NOT possible
         - Not compressed and not running  -> Compression IS possible
        """
        if CrunchyAPI.is_compression_pending(compression_obj):
            return False

        if compression_obj.spring_exists():
            LOG.info("SPRING file found")
            return False

        LOG.info("FASTQ compression is possible")

        return True

    @staticmethod
    def is_spring_decompression_possible(compression_obj: CompressionData) -> bool:
        """Check if SPRING decompression is possible

        There are three possible answers to this question:

            - Compression/Decompression is running      -> Decompression is NOT possible
            - The FASTQ files are not compressed        -> Decompression is NOT possible
            - Compression has been performed            -> Decompression IS possible

        """
        if compression_obj.pending_exists():
            LOG.info("Compression/decompression is pending for %s", compression_obj.run_name)
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
    def is_fastq_compression_done(compression_obj: CompressionData) -> bool:
        """Check if FASTQ compression is finished

        This is checked by controlling that the SPRING files that are produced after FASTQ
        compression exists.

        The following has to be fulfilled for FASTQ compression to be considered done:

            - A SPRING archive file exists
            - A SPRING archive metada file exists
            - The SPRING archive has not been unpacked before FASTQ delta (21 days)

        Note:
        'updated_at' indicates at what date the SPRING archive was unarchived last.
        If the SPRING archive has never been unarchived 'updated_at' is None

        """
        LOG.info("Check if FASTQ compression is finished")
        LOG.info("Check if SPRING file %s exists", compression_obj.spring_path)
        if not compression_obj.spring_exists():
            LOG.info("No SPRING file for %s", compression_obj.run_name)
            return False
        LOG.info("SPRING file found")

        LOG.info("Check if SPRING metadata file %s exists", compression_obj.spring_metadata_path)
        if not compression_obj.metadata_exists():
            LOG.info("No metadata file found")
            return False
        LOG.info("SPRING metadata file found")

        crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(
            compression_obj.spring_metadata_path
        )
        # Check if the SPRING archive has been unarchived
        updated_at: Optional[datetime.date] = get_file_updated_at(crunchy_metadata)
        if updated_at is None:
            LOG.info("FASTQ compression is done for %s", compression_obj.run_name)
            return True

        LOG.info("Files where unpacked %s", updated_at)

        if not CrunchyAPI.check_if_update_spring(updated_at):
            return False

        LOG.info("FASTQ compression is done for %s", compression_obj.run_name)

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

        spring_metadata_path = compression_obj.spring_metadata_path
        LOG.info("Check if SPRING metadata file %s exists", spring_metadata_path)

        if not compression_obj.metadata_exists():
            LOG.info("No SPRING metadata file found")
            return False

        try:
            crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(spring_metadata_path)
        except SyntaxError:
            LOG.info("Malformed metadata content")
            return False

        for file_info in crunchy_metadata.files:
            if not Path(file_info.path).exists():
                LOG.info("File %s does not exist", file_info.path)
                return False
            if not file_info.updated:
                LOG.info("Files have not been unarchived")
                return False

        LOG.info("SPRING decompression is done for run %s", compression_obj.run_name)

        return True

    # These are the compression/decompression methods
    def fastq_to_spring(self, compression_obj: CompressionData, sample_id: str = "") -> None:
        """
        Compress FASTQ files into SPRING by sending to sbatch SLURM

        """
        job_name = "_".join([sample_id, compression_obj.run_name, "fastq_to_spring"])

        log_dir = self.get_log_dir(compression_obj.spring_path)
        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=str(log_dir))

        sbatch_body = self._get_slurm_fastq_to_spring(compression_obj=compression_obj)
        sbatch_path = self.get_sbatch_path(log_dir, "fastq", compression_obj.run_name)
        sbatch_content = "\n".join([sbatch_header, sbatch_body])
        self._submit_sbatch(
            sbatch_content=sbatch_content,
            sbatch_path=sbatch_path,
            pending_path=compression_obj.pending_path,
        )

    def spring_to_fastq(self, compression_obj: CompressionData, sample_id: str = "") -> None:
        """
        Decompress SPRING into FASTQ by submitting sbatch script to SLURM

        """
        crunchy_metadata: CrunchyMetadata = get_crunchy_metadata(
            compression_obj.spring_metadata_path
        )

        job_name = "_".join([sample_id, compression_obj.run_name, "spring_to_fastq"])
        log_dir = self.get_log_dir(compression_obj.spring_path)

        sbatch_header = self._get_slurm_header(job_name=job_name, log_dir=str(log_dir))

        files_info: Dict[str, CrunchyFile] = get_spring_archive_files(crunchy_metadata)

        sbatch_body = self._get_slurm_spring_to_fastq(
            compression_obj=compression_obj,
            checksum_first=files_info["fastq_first"].checksum,
            checksum_second=files_info["fastq_second"].checksum,
        )

        sbatch_path = self.get_sbatch_path(log_dir, "spring", compression_obj.run_name)
        sbatch_content = "\n".join([sbatch_header, sbatch_body])
        self._submit_sbatch(
            sbatch_content=sbatch_content,
            sbatch_path=sbatch_path,
            pending_path=compression_obj.pending_path,
        )

    @staticmethod
    def check_if_update_spring(file_date: datetime.date) -> bool:
        """Check if date is older than FASTQ_DELTA (21 days)"""
        delta = file_date + datetime.timedelta(days=FASTQ_DELTA)
        now = datetime.datetime.now()
        if delta > now.date():
            LOG.info("FASTQ files are not old enough")
            return False
        return True

    # Methods to get file information
    @staticmethod
    def get_log_dir(file_path: Path) -> Path:
        """Return the path to where logs should be stored"""
        return file_path.parent

    @staticmethod
    def get_sbatch_path(log_dir: Path, compression: str, run_name: str = None) -> Path:
        """Return the path to where sbatch should be printed"""
        if compression == "fastq":
            return log_dir / "_".join([run_name, "compress_fastq.sh"])
        # Only other option is "SPRING"
        return log_dir / "_".join([run_name, "decompress_spring.sh"])

    def _submit_sbatch(self, sbatch_content: str, sbatch_path: Path, pending_path: Path):
        """Submit SLURM job"""
        LOG.info("Submit sbatch")
        if self.dry_run:
            LOG.info("Would submit sbatch %s to slurm", sbatch_path)
            return
        LOG.info("Creating pending flag")
        try:
            pending_path.touch(exist_ok=False)
        except FileExistsError:
            LOG.warning("Pending path exists! Do not submit batch job")
            return

        LOG.debug("Pending flag created")
        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters = [str(sbatch_path.resolve())]
        self.process.run_command(parameters=sbatch_parameters)
        if self.process.stderr:
            LOG.info(self.process.stderr)
        if self.process.stdout:
            LOG.info(self.process.stdout)

    def _get_slurm_header(self, job_name: str, log_dir: str) -> str:
        """Create and return a header for a sbatch script"""
        LOG.info("Generating sbatch header")
        ntasks = 12
        mem = 50
        time = 24
        return SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            conda_env=self.crunchy_env,
            mail_user=self.mail_user,
            ntasks=ntasks,
            time=time,
            mem=mem,
        )

    @staticmethod
    def _get_tmp_dir(prefix: str, suffix: str, base: str = None) -> str:
        """Create a temporary directory and return the path to it"""

        with tempfile.TemporaryDirectory(prefix=prefix, suffix=suffix, dir=base) as dir_name:
            tmp_dir_path = dir_name

        LOG.info("Created temporary dir %s", tmp_dir_path)
        return tmp_dir_path

    @staticmethod
    def _get_slurm_fastq_to_spring(compression_obj: CompressionData) -> str:
        """Create and return the body of a sbatch script that runs FASTQ to SPRING"""
        LOG.info("Generating FASTQ to SPRING sbatch body")
        tmp_dir_path = CrunchyAPI._get_tmp_dir(
            prefix="spring_", suffix="_compress", base=compression_obj.analysis_dir
        )
        return SBATCH_FASTQ_TO_SPRING.format(
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            spring_path=compression_obj.spring_path,
            flag_path=compression_obj.spring_metadata_path,
            pending_path=compression_obj.pending_path,
            tmp_dir=tmp_dir_path,
        )

    @staticmethod
    def _get_slurm_spring_to_fastq(
        compression_obj: CompressionData, checksum_first: str, checksum_second: str
    ) -> str:
        """Create and return the body of a sbatch script that runs SPRING to FASTQ"""
        LOG.info("Generating SPRING to FASTQ sbatch body")
        tmp_dir_path = CrunchyAPI._get_tmp_dir(
            prefix="spring_", suffix="_decompress", base=compression_obj.analysis_dir
        )
        return SBATCH_SPRING_TO_FASTQ.format(
            spring_path=compression_obj.spring_path,
            fastq_first=compression_obj.fastq_first,
            fastq_second=compression_obj.fastq_second,
            pending_path=compression_obj.pending_path,
            checksum_first=checksum_first,
            checksum_second=checksum_second,
            tmp_dir=tmp_dir_path,
        )
