"""Class to create sbatch files and communicate with slurm"""
import logging
from pathlib import Path
from typing import List, Optional

from cg.utils import Process
from pydantic import BaseModel
from typing_extensions import Literal

LOG = logging.getLogger(__name__)

SBATCH_HEADER_TEMPLATE = """#! /bin/bash
#SBATCH --job-name={job_name}
#SBATCH --account={account}
#SBATCH --ntasks={number_tasks}
#SBATCH --mem={memory}G
#SBATCH --error={log_dir}/{job_name}.stderr
#SBATCH --output={log_dir}/{job_name}.stdout
#SBATCH --mail-type=FAIL
#SBATCH --mail-user={email}
#SBATCH --time={hours}:{minutes}:00
#SBATCH --qos={priority}

set -eu -o pipefail

log() {{
    NOW=$(date +"%Y%m%d%H%M%S")
    echo "[${{NOW}}] $*"
}}

log "Running on: $(hostname)"
"""

# Double {{ to escape this character
SBATCH_BODY_TEMPLATE = """
error() {{
    {error_body}
    exit 1
}}

trap error ERR

{commands}

"""


class SbatchHeader(BaseModel):
    job_name: str
    account: str
    number_tasks: int
    memory: int
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: Literal["high", "low"] = "low"


class SlurmAPI:
    def __init__(self, config):
        self.process: Process = Process("sbatch")
        self.dry_run: bool = False

    @staticmethod
    def generate_sbatch_header(parameters: SbatchHeader):
        return SBATCH_HEADER_TEMPLATE.format(**parameters.dict())

    @staticmethod
    def generate_sbatch_body(commands: str, error_function: Optional[str] = None):
        if not error_function:
            error_function = "log 'Something went wrong, aborting'"

        return SBATCH_BODY_TEMPLATE.format(**{"error_body": error_function, "commands": commands})

    def submit_sbatch(self, sbatch_content: str, sbatch_path: Path):
        """Submit sbatch file to slurm job"""
        LOG.info("Submit sbatch")
        if self.dry_run:
            LOG.info("Would submit sbatch %s to slurm", sbatch_path)
            return

        with open(sbatch_path, mode="w+t") as sbatch_file:
            sbatch_file.write(sbatch_content)

        sbatch_parameters: List[str] = [str(sbatch_path.resolve())]
        self.process.run_command(parameters=sbatch_parameters)
        if self.process.stderr:
            LOG.info(self.process.stderr)
        if self.process.stdout:
            LOG.info(self.process.stdout)


if __name__ == "__main__":
    config = {
        "job_name": "test",
        "account": "myaccount",
        "number_tasks": 3,
        "memory": 10,
        "log_dir": "path/to/dir",
        "email": "mans@me.com",
        "hours": 2,
    }
    parameters = SbatchHeader.parse_obj(config)
    sbatch_header = SlurmAPI.generate_sbatch_header(parameters)
    from pprint import pprint as pp

    print(sbatch_header)

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
    sbatch_body = SlurmAPI.generate_sbatch_body(
        commands=logic,
    )
    print(sbatch_body)
