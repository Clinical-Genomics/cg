"""
    Module for compressing bam to cram
"""

import logging
import tempfile
from pathlib import Path

from cg.utils import Process
from .constants import (
    BAM_SUFFIX,
    BAM_INDEX_SUFFIX,
    CRAM_SUFFIX,
    CRAM_INDEX_SUFFIX,
    FASTQ_FIRST_SUFFIX,
    FASTQ_SECOND_SUFFIX,
    SPRING_SUFFIX,
)

LOG = logging.getLogger(__name__)


SBATCH_HEADER_TEMPLATE = """
#!/bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks=12
#SBATCH --mem=50G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --time=4:00:00
#SBATCH --qos=low

set e
source activate {crunchy_env}
"""

SBATCH_BAM_TO_CRAM = """
crunchy --reference {reference_path} compress bam --bam-path {bam_path} --cram-path {cram_path}
samtools quickcheck {cram_path}
if [[ $? == 0 ]]
then
    touch {flag_path}
else:
    echo Compression failed
fi
"""

# SBATCH_SPRING = """
# crunchy compress spring --first {fastq_first_path} --second {fastq_second_path} --spring-path {spring_path} --check-integrity
# if [[ $? == 0 ]]
# then
#     touch {flag_path}
# else:
#     echo Compression failed
# fi
# """

FLAG_PATH_SUFFIX = ".crunchy.txt"


class CrunchyAPI:
    """
        API for samtools
    """

    def __init__(self, config: dict):

        self.process = Process("sbatch")
        self.slurm_account = config["crunchy"]["slurm"]["account"]
        self.slurm_log_dir = config["crunchy"]["slurm"]["log_dir"]
        self.crunchy_env = config["crunchy"]["slurm"]["conda_env"]
        self.reference_path = config["crunchy"]["cram_reference"]

    def bam_to_cram(self, bam_path: Path, dry_run: bool = False):
        """
            Compress bam-file into cram
        """
        cram_path = self.change_suffix_bam_to_cram(bam_path)
        job_name = bam_path.name + "_bam_to_cram"
        flag_path = self.get_flag_path(file_path=cram_path)

        sbatch_header = self._get_slurm_header(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=self.slurm_log_dir,
            crunchy_env=self.crunchy_env,
        )

        sbatch_body = self._get_slurm_bam_to_cram(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            reference_path=self.reference_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

    # def spring(
    #     self, fastq_first_path: Path, fastq_second_path: Path, dry_run: bool = False
    # ):
    #     """
    #         Use spring to compress fastq_files
    #     """
    #
    #     spring_path = self.change_suffix_spring(
    #         fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
    #     )
    #     job_name = spring_path.name + "_spring"
    #     flag_path = self.get_flag_path(file_path=spring_path)
    #
    #     sbatch_header = self.get_slurm_header(
    #         job_name=job_name,
    #         account=self.slurm_account,
    #         log_dir=self.slurm_log_dir,
    #         crunchy_env=self.crunchy_env,
    #     )
    #
    #     sbatch_body = self.get_slurm_spring(
    #         fastq_first_path=fastq_first_path,
    #         fastq_second_path=fastq_second_path,
    #         spring_path=spring_path,
    #         flag_path=flag_path,
    #     )
    #
    #     sbatch_content = sbatch_header + "\n" + sbatch_body
    #     self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

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

    def cram_compression_done(self, bam_path: Path) -> bool:
        """Check if cram-compression already done for bam-file"""
        cram_path = self.change_suffix_bam_to_cram(bam_path)
        flag_path = self.get_flag_path(file_path=cram_path)

        if not cram_path.exists():
            LOG.info("No cram-file for %s", bam_path)
            return False
        if not self.get_index_path(cram_path).exists():
            LOG.info("No index-file for %s", cram_path)
            return False
        if not flag_path.exists():
            LOG.info("No %s file for %s", FLAG_PATH_SUFFIX, cram_path)
            return False
        return True

    def bam_compression_possible(self, bam_path: Path) -> bool:
        """Check if it cram compression for bam-file is possible"""
        if bam_path is None or not bam_path.exists():
            LOG.warning("Could not find bam %s", bam_path)
            return False

        if self.cram_compression_done(bam_path=bam_path):
            LOG.info("cram compression already exists for %s", bam_path)
            return False

        return True

    #
    # def spring_compression_done(
    #     self, fastq_first_path: Path, fastq_second_path: Path
    # ) -> bool:
    #     """Check if spring compression already is done for fastq-files"""
    #
    #     spring_path = self.change_suffix_spring(
    #         fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
    #     )
    #     flag_path = spring_path.with_suffix(FLAG_PATH_SUFFIX)
    #
    #     if not spring_path.exists():
    #         LOG.info("No spring file %s", spring_path)
    #         return False
    #     if not flag_path.exists():
    #         LOG.info("No %s file for %s", FLAG_PATH_SUFFIX, spring_path)
    #         return False
    #     return True

    # def fastq_compression_possible(
    #     self, fastq_first_path: Path, fastq_second_path: Path
    # ) -> bool:
    #     """Check if spring compression is possible for fastq-files"""
    #     if fastq_first_path is None or not fastq_first_path.exists():
    #         LOG.warning("Could not find fastq %s", fastq_first_path)
    #         return False
    #     if fastq_second_path is None or not fastq_second_path.exists():
    #         LOG.warning("Could not find fastq %s", fastq_second_path)
    #         return False
    #     if self.spring_compression_done(
    #         fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
    #     ):
    #         return False
    #
    #     return True

    @staticmethod
    def get_flag_path(file_path):
        return file_path.with_suffix(FLAG_PATH_SUFFIX)

    @staticmethod
    def get_index_path(file_path):
        index_type = CRAM_INDEX_SUFFIX
        if file_path.suffix == BAM_SUFFIX:
            index_type = BAM_INDEX_SUFFIX
        return file_path.with_suffix(file_path.suffix + index_type)

    @staticmethod
    def change_suffix_bam_to_cram(bam_path: Path) -> Path:
        """ Change suffix from .bam to .cram"""
        if not bam_path.suffix == BAM_SUFFIX:
            LOG.error("%s does not end with %s", bam_path, BAM_SUFFIX)
            raise ValueError
        cram_path = bam_path.with_suffix(CRAM_SUFFIX)
        return cram_path

    # @staticmethod
    # def change_suffix_spring(fastq_first_path: Path, fastq_second_path: Path) -> Path:
    #     """Make correct suffix for spring compressed fastq-files"""
    #     if not fastq_first_path.name.endswith(FASTQ_FIRST_SUFFIX):
    #         LOG.error("%s does not end with %s", fastq_first_path, FASTQ_FIRST_SUFFIX)
    #         raise ValueError
    #
    #     if not fastq_second_path.name.endswith(FASTQ_SECOND_SUFFIX):
    #         LOG.error("%s does not end with %s", fastq_second_path, FASTQ_SECOND_SUFFIX)
    #         raise ValueError
    #
    #     if not str(fastq_first_path).replace(FASTQ_FIRST_SUFFIX, "") == str(
    #         fastq_second_path
    #     ).replace(FASTQ_SECOND_SUFFIX, ""):
    #         LOG.error(
    #             "%s and %s does not have the same root",
    #             fastq_first_path,
    #             fastq_second_path,
    #         )
    #         raise ValueError
    #
    #     spring_path = Path(
    #         str(fastq_first_path).replace(FASTQ_FIRST_SUFFIX, SPRING_SUFFIX)
    #     )
    #     return spring_path

    @staticmethod
    def _get_slurm_header(
        job_name: str, log_dir: str, account: str, crunchy_env: str
    ) -> str:
        sbatch_header = SBATCH_HEADER_TEMPLATE.format(
            job_name=job_name, account=account, log_dir=log_dir, crunchy_env=crunchy_env
        )
        return sbatch_header

    @staticmethod
    def _get_slurm_bam_to_cram(
        bam_path: str, cram_path: str, flag_path: str, reference_path: str
    ) -> str:
        sbatch_body = SBATCH_BAM_TO_CRAM.format(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            reference_path=reference_path,
        )
        return sbatch_body

    # @staticmethod
    # def _get_slurm_spring(
    #     fastq_first_path: str, fastq_second_path: str, spring_path: str, flag_path: str
    # ) -> str:
    #
    #     sbatch_body = SBATCH_SPRING.format(
    #         fastq_first_path=fastq_first_path,
    #         fastq_second_path=fastq_second_path,
    #         spring_path=spring_path,
    #         flag_path=flag_path,
    #     )
    #     return sbatch_body
