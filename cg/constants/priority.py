"""Priority specific constants."""
from enum import Enum, IntEnum

from cg.utils.enums import StrEnum


class SlurmQos(StrEnum):
    MAINTENANCE: str = "maintenance"
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    EXPRESS: str = "express"


class PriorityTerms(StrEnum):
    EXPRESS: str = "express"
    PRIORITY: str = "priority"
    RESEARCH: str = "research"
    STANDARD: str = "standard"


SLURM_ACCOUNT_TO_QOS = {
    "production": SlurmQos.NORMAL,
    "development": SlurmQos.LOW,
}


class PriorityChoices(str, Enum):
    RESEARCH = "research"
    STANDARD = "standard"
    PRIORITY = "priority"
    EXPRESS = "express"
    CLINICAL_TRIALS = "clinical_trials"


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
