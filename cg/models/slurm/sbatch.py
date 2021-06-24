from typing import Optional

from pydantic import BaseModel
from typing_extensions import Literal

from cg.constants.priority import SlurmQos


class Sbatch(BaseModel):
    job_name: str
    account: str
    number_tasks: int
    memory: int
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: SlurmQos = SlurmQos.LOW
    commands: str
    error: Optional[str]
    exclude: Optional[str] = ""
