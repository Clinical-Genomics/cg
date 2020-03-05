"""
    Module for compressing bam to cram 
"""

import logging
import tempfile
from pathlib import Path

from cg.utils import Process

LOG = logging.getLogger(__name__)


REFERENCE_PATH = "path/to/reference"
SBATCH_SCRIPT_TEMPLATE = """
#!/bin/bash
#SBATCH -J {job_name}
#SBATCH -A production # Maybe this should not be hardcoded if we want to test on stage
#SBATCH -n 1 ...
$SBATCH --mail ...
$SBATCH --stderr ...
$SBATCH --stdout ...

source activate P_samtools # Put samtools in container and run from conda env?

samtools view -c -o {cram_path} -r {reference_path} {bam_path}
samtools index {cram_path} {cram_path}.crai
PRE_CHECKSUM=$(samtools view {bam_path} | md5sum)
POST_CHECKSUM=$(samtools view {cram_path} | md5sum)

if [[ $PRE_CHECKSUM == $POST_CHECKSUM ]]
then
    echo "Compression completed"
    touch {cram_dir}_{job_name}_cram_complete
else
    echo "Compression failed"
    rm {cram_path}
    rm {cram_path}.crai
    exit 1
fi
"""


class BamToCramAPI:
    """
        API for samtools
    """

    def __init__(self):

        self.process = Process("sbatch")

    def bam_to_cram(self, bam_path, job_name, dry_run=False):
        """
            Make sbatch script and send to slurm
        """
        cram_path = self.change_suffix(bam_path)
        cram_dir = str(Path(bam_path).parent)

        sbatch_content = SBATCH_SCRIPT_TEMPLATE.format(
            job_name=job_name,
            bam_path=bam_path,
            cram_path=cram_path,
            reference_path=REFERENCE_PATH,
            cram_dir=cram_dir,
        )
        if not dry_run:
            with tempfile.NamedTemporaryFile(mode="w+t") as bam_to_cram_sbatch:

                bam_to_cram_sbatch.write(sbatch_content)
                bam_to_cram_sbatch.flush()
                sbatch_parameters = [bam_to_cram_sbatch.name]
                LOG.info("compressing %s to cram", bam_path)
                self.process.run_command(sbatch_parameters)
                LOG.info(self.process.stderr)
                LOG.info(self.process.stdout)
        else:
            LOG.info("Would submit following to slurm:\n\n%s", sbatch_content)

    @staticmethod
    def change_suffix(bam_path: str):
        """
            Change .bam -> .cram suffix
        """
        cram_path = bam_path.replace(".bam", ".cram")
        return cram_path
