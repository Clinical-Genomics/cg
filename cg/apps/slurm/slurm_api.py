"""Class to create sbatch files and communicate with slurm"""
import logging
from pathlib import Path
from typing import List, Optional

from cg.apps.slurm.sbatch import SBATCH_BODY_TEMPLATE, SBATCH_HEADER_TEMPLATE
from cg.utils import Process
from pydantic import BaseModel
from typing_extensions import Literal

LOG = logging.getLogger(__name__)


class Sbatch(BaseModel):
    job_name: str
    account: str
    number_tasks: int
    memory: int
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: Literal["high", "low"] = "low"
    commands: str
    error: Optional[str]


class SlurmAPI:
    def __init__(self):
        self.process: Process = Process("sbatch")
        self.dry_run: bool = False

    def set_dry_run(self, dry_run: bool) -> None:
        LOG.info("Set dry run to %s", dry_run)
        self.dry_run = dry_run

    @staticmethod
    def generate_sbatch(parameters: Sbatch) -> str:
        """Take a parameters object and generate a string with sbatch information"""
        sbatch_header: str = SlurmAPI.generate_sbatch_header(parameters=parameters)
        sbatch_body: str = SlurmAPI.generate_sbatch_body(
            commands=parameters.commands, error_function=parameters.error
        )
        return "\n".join([sbatch_header, sbatch_body])

    @staticmethod
    def generate_sbatch_header(parameters: Sbatch) -> str:
        return SBATCH_HEADER_TEMPLATE.format(**parameters.dict())

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
        return int(self.process.stdout.strip())


if __name__ == "__main__":
    config = {
        "job_name": "test",
        "account": "myaccount",
        "number_tasks": 3,
        "memory": 10,
        "log_dir": "path/to/dir",
        "email": "mans@me.com",
        "hours": 2,
        "commands": "genmod",
    }
    parameters = Sbatch.parse_obj(config)
    sbatch_file = SlurmAPI.generate_sbatch(parameters)

    print(sbatch_file)

    error = """
     if [[ -e {spring_path} ]]
     then
        rm {spring_path}
     fi
     
     if [[ -e {pending_path} ]]
     then
         rm {pending_path}
     fi
    """
    logic = """mkdir -p path/to/tmp"""
    parameters.error = error

    sbatch_file = SlurmAPI.generate_sbatch(parameters)

    print(sbatch_file)
