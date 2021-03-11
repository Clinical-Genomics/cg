"""Class to create sbatch files and communicate with slurm"""
import logging
from pathlib import Path
from typing import List, Optional

from cg.apps.slurm.sbatch import SBATCH_BODY_TEMPLATE, SBATCH_HEADER_TEMPLATE
from cg.models.slurm.sbatch import Sbatch
from cg.utils import Process

LOG = logging.getLogger(__name__)


class SlurmAPI:
    def __init__(self):
        self.process: Process = Process("sbatch")
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    @staticmethod
    def generate_sbatch(sbatch_parameters: Sbatch) -> str:
        """Take a parameters object and generate a string with sbatch information"""
        sbatch_header: str = SlurmAPI.generate_sbatch_header(sbatch_parameters=sbatch_parameters)
        sbatch_body: str = SlurmAPI.generate_sbatch_body(
            commands=sbatch_parameters.commands, error_function=sbatch_parameters.error
        )
        return "\n".join([sbatch_header, sbatch_body])

    @staticmethod
    def generate_sbatch_header(sbatch_parameters: Sbatch) -> str:
        return SBATCH_HEADER_TEMPLATE.format(**sbatch_parameters.dict())

    @staticmethod
    def generate_sbatch_body(commands: str, error_function: Optional[str] = None) -> str:
        if not error_function:
            error_function = "log 'Something went wrong, aborting'"

        return SBATCH_BODY_TEMPLATE.format(**{"error_body": error_function, "commands": commands})

    def submit_sbatch(self, sbatch_content: str, sbatch_path: Path) -> int:
        """Submit sbatch file to slurm job.

        Return the slurm job id
        """
        LOG.info("Submit sbatch")
        if self.dry_run:
            LOG.info("Would submit sbatch %s to slurm", sbatch_path)
            return 123456

        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters: List[str] = [str(sbatch_path.resolve())]
        self.process.run_command(parameters=sbatch_parameters)
        if self.process.stderr:
            LOG.info(self.process.stderr)
        LOG.info(self.process.stdout)

        try:
            job_number: int = int(self.process.stdout.strip().split()[-1])
        except ValueError:
            LOG.warning("Could not get slurm job number")
            job_number = 0
        return job_number
