"""Priority specific constants"""
from enum import IntEnum

from cg.utils.enums import StrEnum


class SlurmQos(StrEnum):
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    EXPRESS: str = "express"


SLURM_ACCOUNT_TO_QOS = {
    "production": SlurmQos.NORMAL,
    "development": SlurmQos.LOW,
}


class Priority(IntEnum):
    research: int = 0
    standard: int = 1
    priority: int = 2
    express: int = 3
    clinical_trials: int = 4


PRIORITY_TO_SLURM_QOS = {
    Priority.research: SlurmQos.LOW,
    Priority.standard: SlurmQos.NORMAL,
    Priority.priority: SlurmQos.HIGH,
    Priority.express: SlurmQos.EXPRESS,
    Priority.clinical_trials: SlurmQos.NORMAL,
}
