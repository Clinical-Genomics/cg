"""Module to create sbatch files and communicate with SLURM."""

import logging
from pathlib import Path
from typing import Any

from cg.apps.slurm.sbatch import (
    DRAGEN_SBATCH_HEADER_TEMPLATE,
    SBATCH_BODY_TEMPLATE,
    SBATCH_HEADER_TEMPLATE,
)
from cg.models.slurm.sbatch import Sbatch, SbatchDragen
from cg.utils import Process

LOG = logging.getLogger(__name__)


class SlurmAPI:
    """API to SLURM."""

    def __init__(self):
        """Initialize SlurmAPI class."""
        self.process: Process = Process(binary="sbatch")
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        """Set dry run."""
        LOG.debug(f"SlurmAPI: Set dry run to {dry_run}")
        self.dry_run = dry_run

    @staticmethod
    def generate_sbatch_content(sbatch_parameters: Sbatch) -> str:
        """Take a parameters object and generate a string with sbatch information."""
        if isinstance(sbatch_parameters, SbatchDragen):
            sbatch_header: str = SlurmAPI.generate_dragen_sbatch_header(
                sbatch_parameters=sbatch_parameters
            )
        else:
            sbatch_header: str = SlurmAPI.generate_sbatch_header(
                sbatch_parameters=sbatch_parameters
            )
        sbatch_body: str = SlurmAPI.generate_sbatch_body(
            commands=sbatch_parameters.commands, error_function=sbatch_parameters.error
        )
        return "\n".join([sbatch_header, sbatch_body])

    @staticmethod
    def generate_sbatch_header(sbatch_parameters: Sbatch) -> str:
        header_params: dict[str, Any] = sbatch_parameters.model_dump()
        optional_headers: str = _generate_optional_headers(
            [sbatch_parameters.exclude, sbatch_parameters.dependency]
        )

        return SBATCH_HEADER_TEMPLATE.format(**header_params, optional_headers=optional_headers)

    @staticmethod
    def generate_dragen_sbatch_header(sbatch_parameters: Sbatch) -> str:
        return DRAGEN_SBATCH_HEADER_TEMPLATE.format(**sbatch_parameters.model_dump())

    @staticmethod
    def generate_sbatch_body(commands: str, error_function: str | None = None) -> str:
        if not error_function:
            error_function = "log 'Something went wrong, aborting'"

        return SBATCH_BODY_TEMPLATE.format(**{"error_body": error_function, "commands": commands})

    @staticmethod
    def write_sbatch_file(sbatch_content: str, sbatch_path: Path, dry_run: bool) -> None:
        if dry_run:
            LOG.info(f"Write sbatch content to path {sbatch_path}: \n{sbatch_content}")
            return
        LOG.debug(f"Write sbatch content {sbatch_content} to {sbatch_path}")
        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

    def submit_sbatch_job(self, sbatch_path: Path) -> int:
        LOG.info(f"Submit sbatch {sbatch_path}")
        sbatch_parameters: list[str] = [str(sbatch_path)]
        self.process.run_command(parameters=sbatch_parameters, dry_run=self.dry_run)
        if self.process.stderr:
            LOG.info(self.process.stderr)
        LOG.info(self.process.stdout)
        try:
            job_number: int = int(self.process.stdout.strip().split()[-1])
        except (ValueError, IndexError):
            LOG.warning("Could not get slurm job number")
            job_number = 0
            if self.dry_run:
                job_number = 123456
        return job_number

    def submit_sbatch(self, sbatch_content: str, sbatch_path: Path) -> int:
        """Submit sbatch file to slurm.

        Return the slurm job id
        """
        SlurmAPI.write_sbatch_file(
            sbatch_content=sbatch_content, sbatch_path=sbatch_path, dry_run=self.dry_run
        )
        return self.submit_sbatch_job(sbatch_path=sbatch_path)


def _generate_optional_headers(optional_headers: list[str | None]) -> str:
    header_str: str = ""
    for header in optional_headers:
        header_str += f"#SBATCH {header}\n" if header else ""
    return header_str
