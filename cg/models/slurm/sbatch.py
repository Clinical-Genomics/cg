from typing import Optional

from pydantic import BaseModel

from cg.constants.constants import HastaSlurmPartitions
from cg.constants.priority import SlurmQos


class Sbatch(BaseModel):
    use_login_shell: Optional[str] = ""
    job_name: str
    account: str
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    quality_of_service: SlurmQos = SlurmQos.LOW
    commands: str
    error: Optional[str]
    exclude: Optional[str] = ""
    number_tasks: Optional[int]
    memory: Optional[int]


class SbatchDragen(Sbatch):
    partition: str = HastaSlurmPartitions.DRAGEN
    nodes: int = 1
    cpus_per_task: int = 24
