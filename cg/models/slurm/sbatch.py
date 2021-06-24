from typing import Optional

from pydantic import BaseModel

from cg.constants.priority import SlurmQos


class Sbatch(BaseModel):
    job_name: str
    account: str
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: SlurmQos = SlurmQos.LOW
    commands: str
    error: Optional[str]
    exclude: Optional[str] = ""
    number_tasks: int
    memory: int


class SbatchDragen(BaseModel):
    job_name: str
    account: str
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: SlurmQos = SlurmQos.LOW
    commands: str
    error: Optional[str]
    exclude: Optional[str] = ""
    partition: str = "dragen"
    nodes: int = 1
    cpus_per_task: int = 24
