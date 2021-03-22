from typing import Optional

from pydantic import BaseModel
from typing_extensions import Literal


class Sbatch(BaseModel):
    job_name: str
    account: str
    number_tasks: int
    memory: int
    log_dir: str
    email: str
    hours: int
    minutes: str = "00"
    priority: Literal["high", "normal", "low"] = "low"
    commands: str
    error: Optional[str]
