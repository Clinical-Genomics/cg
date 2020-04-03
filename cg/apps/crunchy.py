"""
    Module for compressing BAM to CRAM
"""

import logging
import tempfile
from pathlib import Path

from cg.constants import (BAM_INDEX_SUFFIX, BAM_SUFFIX, CRAM_INDEX_SUFFIX,
                          CRAM_SUFFIX, FASTQ_FIRST_READ_SUFFIX,
                          FASTQ_SECOND_READ_SUFFIX, SPRING_SUFFIX)
from cg.utils import Process

LOG = logging.getLogger(__name__)


SBATCH_HEADER_TEMPLATE = """#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={ntasks}
#SBATCH --mem={mem}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={mail_user}
#SBATCH --time=4:00:00
#SBATCH --qos=low

set -e

echo "Running on: $(hostname)"

source activate {conda_env}
"""

SBATCH_BAM_TO_CRAM = """
error() {{
    if [[ -e {cram_path} ]]
    then
        rm {cram_path}
    fi

    if [[ -e {cram_path}.crai ]]
    then
        rm {cram_path}.crai
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -r {reference_path} -t 12 compress bam -b {bam_path} -c {cram_path}
samtools quickcheck {cram_path}
touch {flag_path}
rm {pending_path}"""

SBATCH_SPRING = """
error() {{
    if [[ -e {spring_path} ]]
    then
        rm {spring_path}
    fi

    if [[ -e {pending_path} ]]
    then
        rm {pending_path}
    fi

    exit 1
}}

trap error ERR

touch {pending_path}
crunchy -t 12 compress fastq -f {fastq_first} -s {fastq_second} -o {spring_path} --check-integrity
touch {flag_path}
rm {pending_path}"""

FLAG_PATH_SUFFIX = ".crunchy.txt"
PENDING_PATH_SUFFIX = ".crunchy.pending.txt"


class CrunchyAPI:
    """
        API for samtools
    """

    def __init__(self, config: dict):

        self.process = Process("sbatch")
        self.slurm_account = config["crunchy"]["slurm"]["account"]
        self.crunchy_env = config["crunchy"]["slurm"]["conda_env"]
        self.mail_user = config["crunchy"]["slurm"]["mail_user"]
        self.reference_path = config["crunchy"]["cram_reference"]

    def bam_to_cram(self, bam_path: Path, ntasks: int, mem: int, dry_run: bool = False):
        """
            Compress BAM file into CRAM
        """
        cram_path = self.get_cram_path_from_bam(bam_path)
        job_name = bam_path.name + "_bam_to_cram"
        flag_path = self.get_flag_path(file_path=cram_path)
        pending_path = self.get_pending_path(file_path=bam_path)
        log_dir = bam_path.parent

        sbatch_header = self._get_slurm_header(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            mail_user=self.mail_user,
            conda_env=self.crunchy_env,
            ntasks=ntasks,
            mem=mem,
        )

        sbatch_body = self._get_slurm_bam_to_cram(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            pending_path=pending_path,
            reference_path=self.reference_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

    def fastq_to_spring(
        self,
        fastq_first_path: Path,
        fastq_second_path: Path,
        ntasks: int,
        mem: int,
        dry_run: bool = False,
    ):
        """
            Compress FASTQ files into SPRING
        """
        spring_path = self.get_spring_path_from_fastqs(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        )
        job_name = str(fastq_first_path.name).replace(FASTQ_FIRST_READ_SUFFIX, "_fastq_to_spring")
        flag_path = self.get_flag_path(file_path=fastq_first_path)
        pending_path = self.get_pending_path(file_path=fastq_first_path)
        log_dir = spring_path.parent

        sbatch_header = self._get_slurm_header(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=log_dir,
            mail_user=self.mail_user,
            conda_env=self.crunchy_env,
            ntasks=ntasks,
            mem=mem,
        )

        sbatch_body = self._get_slurm_fastq_to_spring(
            fastq_first_path=fastq_first_path,
            fastq_second_path=fastq_second_path,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

    def _submit_sbatch(self, sbatch_content: str, dry_run: bool = False):
        """Submit slurm job"""
        if not dry_run:
            with tempfile.NamedTemporaryFile(mode="w+t") as sbatch_file:

                sbatch_file.write(sbatch_content)
                sbatch_file.flush()
                sbatch_parameters = [sbatch_file.name]
                self.process.run_command(sbatch_parameters)
                LOG.info(self.process.stderr)
                LOG.info(self.process.stdout)
        else:
            LOG.info("Would submit following to slurm:\n\n%s", sbatch_content)

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

    def is_spring_compression_done(self, fastq_first_path: Path, fastq_second_path: Path) -> bool:
        """Check if CRAM compression already done for BAM file"""
        spring_path = self.get_spring_path_from_fastqs(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        )
        flag_path = self.get_flag_path(file_path=fastq_first_path)

        if not spring_path.exists():
            LOG.info("No SPRING file for %s and %s", fastq_first_path, fastq_second_path)
            return False
        if not flag_path.exists():
            LOG.info(
                "No %s file for %s and %s", FLAG_PATH_SUFFIX, fastq_first_path, fastq_second_path
            )
            return False
        return True

    def is_spring_compression_pending(
        self, fastq_first_path: Path, fastq_second_path: Path
    ) -> bool:
        """Check if cram compression has started, but not yet finished"""
        pending_path = self.get_pending_path(file_path=fastq_first_path)
        if pending_path.exists():
            LOG.info(
                "SPRING compression is pending for %s and %s", fastq_first_path, fastq_second_path
            )
            return True
        return False

    def is_fastq_compression_possible(
        self, fastq_first_path: Path, fastq_second_path: Path
    ) -> bool:
        """Check if it CRAM compression for BAM file is possible"""
        if fastq_first_path is None or not fastq_first_path.exists():
            LOG.warning("Could not find fastq %s", fastq_first_path)
            return False
        if fastq_second_path is None or not fastq_second_path.exists():
            LOG.warning("Could not find fastq %s", fastq_second_path)
            return False
        if self.is_spring_compression_done(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        ):
            LOG.info(
                "SPRING compression already exists for %s and %s",
                fastq_first_path,
                fastq_second_path,
            )
            return False
        return True

    @staticmethod
    def get_flag_path(file_path):
        """Get path to 'finished' flag"""

        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_FIRST_READ_SUFFIX, FLAG_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_SECOND_READ_SUFFIX, FLAG_PATH_SUFFIX))
        return file_path.with_suffix(FLAG_PATH_SUFFIX)

    @staticmethod
    def get_pending_path(file_path):
        """Gives path to pending-flag path"""
        if str(file_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_FIRST_READ_SUFFIX, PENDING_PATH_SUFFIX))
        if str(file_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            return Path(str(file_path).replace(FASTQ_SECOND_READ_SUFFIX, PENDING_PATH_SUFFIX))
        return file_path.with_suffix(PENDING_PATH_SUFFIX)

    @staticmethod
    def get_index_path(file_path):
        """Get possible paths for index
            Args:
                file_path (Path): path to BAM or CRAM
            Returns (dict): path with single_suffix, e.g. .bai
                and path with double_suffix, e.g. .bam.bai
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
    def get_spring_path_from_fastqs(
        fastq_first_path: Path, fastq_second_path: Path
    ) -> Path:
        """ GET corresponding SPRING file path from paired FASTQ file paths"""
        if not str(fastq_first_path).endswith(FASTQ_FIRST_READ_SUFFIX):
            LOG.error(
                "%s does not end with %s", fastq_first_path, FASTQ_FIRST_READ_SUFFIX
            )
            raise ValueError
        if not str(fastq_second_path).endswith(FASTQ_SECOND_READ_SUFFIX):
            LOG.error(
                "%s does not end with %s", fastq_second_path, FASTQ_SECOND_READ_SUFFIX
            )
            raise ValueError
        spring_path = Path(
            str(fastq_first_path).replace(FASTQ_FIRST_READ_SUFFIX, SPRING_SUFFIX)
        )
        return spring_path

    @staticmethod
    def _get_slurm_header(
        job_name: str,
        log_dir: str,
        account: str,
        mail_user: str,
        conda_env: str,
        ntasks: int,
        mem: int,
    ) -> str:
        sbatch_header = SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name,
            account=account,
            log_dir=log_dir,
            conda_env=conda_env,
            mail_user=mail_user,
            ntasks=ntasks,
            mem=mem,
        )
        return sbatch_header

    @staticmethod
    def _get_slurm_bam_to_cram(
        bam_path: str,
        cram_path: str,
        flag_path: str,
        pending_path: str,
        reference_path: str,
    ) -> str:
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
        sbatch_body = SBATCH_SPRING.format(
            fastq_first=fastq_first_path,
            fastq_second=fastq_second_path,
            spring_path=spring_path,
            flag_path=flag_path,
            pending_path=pending_path,
        )

        return sbatch_body
