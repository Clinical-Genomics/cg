"""
    Module for compressing bam to cram
"""

import logging
import tempfile
from pathlib import Path

from cg.utils import Process

LOG = logging.getLogger(__name__)


SBATCH_HEADER_TEMPLATE = """
#!/bin/bash
#SBATCH -J {job_name}
#SBATCH -A {account}
#SBATCH -n 1
$SBATCH --stderr {log_dir}/{jobname}.stderr
$SBATCH --stdout {log_dir}/{jobname}.stdout

source activate {crunchy_env}
"""

SBATCH_BAM_TO_CRAM = """
crunchy compress bam --bam-path {bam_path} --cram-path {cram_path} --reference {reference_path} --check-integrity
if [[ $? == 0 ]]
then
    touch {flag_path}
else:
    echo "Compression failed"
fi
"""


SBATCH_SPRING = """
crunchy compress spring --first {fastq_first_path} --second {fastq_second_path} --spring-path {spring_path} --check-integrity
if [[ $? == 0 ]]
then
    touch {flag_path}
else:
    echo "Compression failed"
fi
"""


def get_slurm_header(
    job_name: str, log_dir: str, account: str, crunchy_env: str
) -> str:
    sbatch_header = SBATCH_HEADER_TEMPLATE.format(
        job_name=job_name, account=account, log_dir=log_dir, crunchy_env=crunchy_env
    )
    return sbatch_header


def get_slurm_bam_to_cram(
    bam_path: str, cram_path: str, flag_path: str, reference_path: str
) -> str:
    sbatch_body = SBATCH_BAM_TO_CRAM.format(
        bam_path=bam_path,
        cram_path=cram_path,
        flag_path=flag_path,
        reference_path=reference_path,
    )
    return sbatch_body


def get_slurm_spring(
    fastq_first_path: str, fastq_second_path: str, spring_path: str, flag_path: str
) -> str:

    sbatch_body = SBATCH_SPRING.format(
        fastq_first_path=fastq_first_path,
        fastq_second_path=fastq_second_path,
        spring_path=spring_path,
        flag_path=flag_path,
    )
    return sbatch_body


FLAG_PATH_SUFFIX = "crunchy.txt"
BAM_SUFFIX = ".bam"
CRAM_SUFFIX = ".cram"
FASTQ_FIRST_SUFFIX = "R1_001.fastq.gz"
FASTQ_SECOND_SUFFIX = "R2_001.fastq.gz"


class Crunchy:
    """
        API for samtools
    """

    def __init__(self, config: dict):

        self.process = Process("sbatch")
        self.slurm_account = config["crunchy"]["slurm"]["account"]
        self.slurm_log_dir = config["cruncy"]["slurm"]["log_dir"]
        self.crunchy_env = config["crunchy"]["conda_env"]
        self.reference_path = config["crunchy"]["cram_reference"]

    def bam_to_cram(self, bam_path: str, dry_run: bool = False):
        """
            Make sbatch script and send to slurm
        """
        cram_path = self.change_suffix_bam_to_cram(bam_path)
        job_name = Path(cram_path).name + "_bam_to_cram"
        flag_path = cram_path + FLAG_PATH_SUFFIX

        sbatch_header = get_slurm_header(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=self.slurm_log_dir,
            crunchy_env=self.crunchy_env,
        )

        sbatch_body = get_slurm_bam_to_cram(
            bam_path=bam_path,
            cram_path=cram_path,
            flag_path=flag_path,
            reference_path=self.reference_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

    def spring(
        self, fastq_first_path: str, fastq_second_path: str, dry_run: bool = False
    ):

        spring_path = self.change_suffix_spring(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        )
        job_name = Path(spring_path).name + "_spring"
        flag_path = spring_path + FLAG_PATH_SUFFIX

        sbatch_header = get_slurm_header(
            job_name=job_name,
            account=self.slurm_account,
            log_dir=self.slurm_log_dir,
            crunchy_env=self.crunchy_env,
        )

        sbatch_body = get_slurm_spring(
            fastq_first_path=fastq_first_path,
            fastq_second_path=fastq_second_path,
            spring_path=spring_path,
            flag_path=flag_path,
        )

        sbatch_content = sbatch_header + "\n" + sbatch_body
        self._submit_sbatch(sbatch_content=sbatch_content, dry_run=dry_run)

    def _submit_sbatch(self, sbatch_content: str, dry_run: bool = False):
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

    def compression_successful_cram(self, bam_path: str) -> bool:

        cram_path = self.change_suffix_bam_to_cram(bam_path)
        flag_path = cram_path + ".crunchy.txt"

        if not Path(cram_path).exists():
            LOG.info("No cram-file for %s", bam_path)
            return False
        if not Path(cram_path + ".crai").exists():
            LOG.info("No crai-file for %s", cram_path)
            return False
        if not Path(flag_path).exists():
            LOG.info("No .crunchy.txt file for %s", cram_path)
            return False

        LOG.info("bam to cram conversion successful for %s", bam_path)
        return True

    def compression_successful_spring(
        self, fastq_first_path: str, fastq_second_path: str
    ) -> bool:

        spring_path = self.change_suffix_spring(
            fastq_first_path=fastq_first_path, fastq_second_path=fastq_second_path
        )
        flag_path = spring_path + FLAG_PATH_SUFFIX

        if not Path(spring_path).exists():
            LOG.info("No spring file %s", spring_path)
            return False
        if not Path(flag_path).exists():
            LOG.info("No .crunchy.txt file for %s", spring_path)
            return False

        LOG.info(
            "spring compression successful for %s, %s",
            fastq_first_path,
            fastq_second_path,
        )
        return True

    @staticmethod
    def change_suffix_bam_to_cram(bam_path: str) -> str:
        if not bam_path.endswith(BAM_SUFFIX):
            LOG.error("%s does not end with %s", bam_path, BAM_SUFFIX)
            raise ValueError
        cram_path = bam_path[0:-4] + CRAM_SUFFIX
        return cram_path

    @staticmethod
    def change_suffix_spring(fastq_first_path: str, fastq_second_path: str) -> str:

        if not fastq_first_path.endswith(FASTQ_FIRST_SUFFIX):
            LOG.error("%s does not end with %s", fastq_first_path, FASTQ_FIRST_SUFFIX)
            raise ValueError

        if not fastq_second_path.endswith(FASTQ_SECOND_SUFFIX):
            LOG.error("%s does not end with %s", fastq_second_path, FASTQ_SECOND_SUFFIX)
            raise ValueError

        spring_path = fastq_first_path.replace(FASTQ_FIRST_SUFFIX, ".spring")
        return spring_path
