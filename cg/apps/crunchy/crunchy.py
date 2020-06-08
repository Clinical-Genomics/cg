"""
    Module for compressing BAM to CRAM
"""

import logging
from pathlib import Path

from cg.constants import (
    BAM_INDEX_SUFFIX,
    BAM_SUFFIX,
    CRAM_INDEX_SUFFIX,
    CRAM_SUFFIX,
    FASTQ_FIRST_READ_SUFFIX,
    FASTQ_SECOND_READ_SUFFIX,
    SPRING_SUFFIX,
)
from cg.utils import Process

from .sbatch import SBATCH_BAM_TO_CRAM, SBATCH_HEADER_TEMPLATE, SBATCH_SPRING

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

    def set_dry_run(self, dry_run: bool):
        """Update dry run"""
        self.dry_run = dry_run

    def bam_to_cram(self, bam_path: Path, ntasks: int, mem: int):
        """
            Compress BAM file into CRAM
        """
        cram_path = self.get_cram_path_from_bam(bam_path)
        job_name = bam_path.name + "_bam_to_cram"
        flag_path = self.get_flag_path(file_path=cram_path)
        pending_path = self.get_pending_path(file_path=bam_path)
        log_dir = self.get_log_dir(bam_path)

        sbatch_header = self._get_slurm_header(
            job_name=job_name, log_dir=log_dir, ntasks=ntasks, mem=mem,
        )

        sbatch_body = self._get_slurm_bam_to_cram(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            pending_path=pending_path,
            reference_path=self.reference_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        sbatch_path = self.get_sbatch_path(log_dir, "bam")
        self._submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def fastq_to_spring(
        self, fastq_first: Path, fastq_second: Path, ntasks: int, mem: int,
    ):
        """
            Compress FASTQ files into SPRING by sending to sbatch SLURM
        """
        spring_path = self.get_spring_path_from_fastq(fastq=fastq_first)
        job_name = str(fastq_first.name).replace(FASTQ_FIRST_READ_SUFFIX, "_fastq_to_spring")
        flag_path = self.get_flag_path(file_path=spring_path)
        pending_path = self.get_pending_path(file_path=fastq_first)
        log_dir = self.get_log_dir(spring_path)
        # Time to complete job
        time = 24

        sbatch_header = self._get_slurm_header(
            job_name=job_name, log_dir=log_dir, ntasks=ntasks, mem=mem, time=time
        )

        sbatch_body = self._get_slurm_fastq_to_spring(
            fastq_first_path=fastq_first,
            fastq_second_path=fastq_second,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        sbatch_path = self.get_sbatch_path(log_dir, "fastq")
        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, sbatch_path=sbatch_path)

    def _submit_sbatch(self, sbatch_content: str, sbatch_path: Path):
        """Submit slurm job"""
        if self.dry_run:
            LOG.info("Would submit following to slurm:\n\n%s", sbatch_content)
            return
        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters = [str(sbatch_path.resolve())]
        self.process.run_command(sbatch_parameters)
        LOG.info(self.process.stderr)
        LOG.info(self.process.stdout)

    @staticmethod
    def get_log_dir(file_path: Path) -> Path:
        """Return the path to where logs should be stored"""
        return file_path.parent

    @staticmethod
    def get_sbatch_path(log_dir: Path, compression: str) -> Path:
        """Return the path to where sbatch should be printed"""
        if compression == "fastq":
            return log_dir / "compress_fastq.sh"
        return log_dir / "compress_bam.sh"

    def is_cram_compression_done(self, bam_path: Path) -> bool:
        """Check if CRAM compression already done for BAM file"""
        cram_path = self.get_cram_path_from_bam(bam_path)
        flag_path = self.get_flag_path(file_path=cram_path)

        if not cram_path.exists():
            LOG.info("No cram-file for %s", bam_path)
            return False
        index_paths = self.get_index_path(cram_path)
        index_single_suffix = index_paths["single_suffix"]
        index_double_suffix = index_paths["double_suffix"]
        if (not index_single_suffix.exists()) and (not index_double_suffix.exists()):
            LOG.info("No index-file for %s", cram_path)
            return False
        if not flag_path.exists():
            LOG.info("No %s file for %s", FLAG_PATH_SUFFIX, cram_path)
            return False
        return True

    def is_cram_compression_pending(self, bam_path: Path) -> bool:
        """Check if cram compression has started, but not yet finished"""
        pending_path = self.get_pending_path(file_path=bam_path)
        if pending_path.exists():
            LOG.info("Cram compression is pending for %s", bam_path)
            return True
        return False

    def is_bam_compression_possible(self, bam_path: Path) -> bool:
        """Check if it CRAM compression for BAM file is possible"""
        if bam_path is None or not bam_path.exists():
            LOG.warning("Could not find bam %s", bam_path)
            return False
        if self.is_cram_compression_done(bam_path=bam_path):
            LOG.info("cram compression already exists for %s", bam_path)
            return False
        return True

    def is_spring_compression_done(self, fastq_first: Path, fastq_second: Path) -> bool:
        """Check if spring compression if finished"""
        spring_path = self.get_spring_path_from_fastq(fastq=fastq_first)
        LOG.info("Check is spring file %s exists", spring_path)

        if not spring_path.exists():
            LOG.info("No SPRING file for %s and %s", fastq_first, fastq_second)
            return False

        flag_path = self.get_flag_path(file_path=spring_path)
        if not flag_path.exists():
            LOG.info(
                "No %s file for %s and %s", FLAG_PATH_SUFFIX, fastq_first, fastq_second,
            )
            return False
        return True

    def is_spring_compression_pending(self, fastq: Path) -> bool:
        """Check if spring compression has started, but not yet finished"""
        pending_path = self.get_pending_path(file_path=fastq)
        if pending_path.exists():
            LOG.info("SPRING compression is pending for %s", fastq)
            return True
        return False

    @staticmethod
    def get_flag_path(file_path):
        """Get path to 'finished' flag.
        When compressing fastq this means that a .json metadata file has been created
        Otherwise, for bam compression, a regular flag path is returned.
        """
        if file_path.suffix == ".spring":
            return file_path.with_suffix("").with_suffix(".json")

        return file_path.with_suffix(FLAG_PATH_SUFFIX)

    @staticmethod
    def get_pending_path(file_path: Path) -> Path:
        """Gives path to pending-flag path

        There are two cases, either fastq or bam. They are treated as shown below
        """
        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_FIRST_READ_SUFFIX, PENDING_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_SECOND_READ_SUFFIX, PENDING_PATH_SUFFIX))
        return file_path.with_suffix(PENDING_PATH_SUFFIX)

    @staticmethod
    def get_index_path(file_path: Path) -> dict:
        """Get possible paths for index

        Returns:
            dict: path with single_suffix, e.g. .bai and path with double_suffix, e.g. .bam.bai
        """
        index_type = CRAM_INDEX_SUFFIX
        if file_path.suffix == BAM_SUFFIX:
            index_type = BAM_INDEX_SUFFIX
        with_single_suffix = file_path.with_suffix(index_type)
        with_double_suffix = file_path.with_suffix(file_path.suffix + index_type)
        return {
            "single_suffix": with_single_suffix,
            "double_suffix": with_double_suffix,
        }

    @staticmethod
    def get_cram_path_from_bam(bam_path: Path) -> Path:
        """ Get corresponding CRAM file path from bam file path """
        if not bam_path.suffix == BAM_SUFFIX:
            LOG.error("%s does not end with %s", bam_path, BAM_SUFFIX)
            raise ValueError
        cram_path = bam_path.with_suffix(CRAM_SUFFIX)
        return cram_path

    @staticmethod
    def get_spring_path_from_fastq(fastq: Path) -> Path:
        """ GET corresponding SPRING file path from a FASTQ file"""
        suffix = FASTQ_FIRST_READ_SUFFIX
        if FASTQ_SECOND_READ_SUFFIX in str(fastq):
            suffix = FASTQ_SECOND_READ_SUFFIX

        spring_path = Path(str(fastq).replace(suffix, "")).with_suffix(SPRING_SUFFIX)
        return spring_path

    def _get_slurm_header(
        self, job_name: str, log_dir: str, ntasks: int, mem: int, time: int = 4
    ) -> str:
        """Create and return a header for a sbatch script"""
        sbatch_header = SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            conda_env=self.crunchy_env,
            mail_user=self.mail_user,
            ntasks=ntasks,
            time=time,
            mem=mem,
        )
        return sbatch_header

    @staticmethod
    def _get_slurm_bam_to_cram(
        bam_path: str, cram_path: str, flag_path: str, pending_path: str, reference_path: str,
    ) -> str:
        """Create and return the body of a sbatch script that runs bam to cram"""
        sbatch_body = SBATCH_BAM_TO_CRAM.format(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            pending_path=pending_path,
            reference_path=reference_path,
        )
        return sbatch_body

    @staticmethod
    def _get_slurm_fastq_to_spring(
        fastq_first_path: str,
        fastq_second_path: str,
        spring_path: str,
        flag_path: str,
        pending_path: str,
    ) -> str:
        """Create and return the body of a sbatch script that runs bam to cram"""
        sbatch_body = SBATCH_SPRING.format(
            fastq_first=fastq_first_path,
            fastq_second=fastq_second_path,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        return sbatch_body
