"""Priority specific constants"""
from enum import Enum

from cgmodels.cg.constants import StrEnum


class SlurmQos(StrEnum):
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    EXPRESS: str = "express"


SLURM_ACCOUNT_TO_QOS = {
    "production": SlurmQos.NORMAL,
    "development": SlurmQos.LOW,
}


class IntEnum(int, Enum):
    def __str__(self) -> str:
        return int.__str__(self)


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
    Priority.clinical_trials: SlurmQos.LOW,
}
