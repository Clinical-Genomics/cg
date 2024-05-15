from pydantic import BaseModel

from cg.constants.constants import HastaSlurmPartitions
from cg.constants.priority import SlurmQos


class Sbatch(BaseModel):
    use_login_shell: str | None = ""
    job_name: str
    account: str
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    quality_of_service: SlurmQos = SlurmQos.LOW
    commands: str
    error: str | None = None
    exclude: str | None = ""
    number_tasks: int | None = None
    memory: int | None = None


class SbatchDragen(Sbatch):
    partition: str = HastaSlurmPartitions.DRAGEN
    nodes: int = 1
    cpus_per_task: int = 24
