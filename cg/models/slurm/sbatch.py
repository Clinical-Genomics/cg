from typing import Optional

from pydantic import BaseModel
from typing_extensions import Literal


class Sbatch(BaseModel):
    job_name: str
    account: str
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: Literal["high", "normal", "low"] = "low"
    commands: str
    error: Optional[str]


class SbatchHasta(Sbatch):
    number_tasks: int
    memory: int


class SbatchDragen(Sbatch):
    partition: str = "dragen"
    nodes: int = 1
    cpus_per_task: int = 24
