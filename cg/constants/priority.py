"""Priority specific constants"""

from enum import IntEnum, StrEnum


class SlurmQos(StrEnum):
    MAINTENANCE: str = "maintenance"
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    EXPRESS: str = "express"


class TrailblazerPriority(StrEnum):
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
    EXPRESS: str = "express"


class PriorityTerms(StrEnum):
    EXPRESS: str = "express"
    PRIORITY: str = "priority"
    RESEARCH: str = "research"
    STANDARD: str = "standard"
    CLINICAL_TRIALS: str = "clinical_trials"


class Priority(IntEnum):
    research: int = 0
    standard: int = 1
    priority: int = 2
    express: int = 3
    clinical_trials: int = 4

    @classmethod
    def priority_to_slurm_qos(cls) -> dict[int, str]:
        return {
            Priority.research: SlurmQos.LOW,
            Priority.standard: SlurmQos.NORMAL,
            Priority.priority: SlurmQos.HIGH,
            Priority.express: SlurmQos.EXPRESS,
            Priority.clinical_trials: SlurmQos.NORMAL,
        }

    # def int_to_priority(self, value: int) -> Priority:
    #     priority_mapping: dict[int, str] = {value: key for key, value in Priority.__dict__.items() if not key.startswith("__")}
    #     return priority_mapping[value]


class SlurmAccount(StrEnum):
    PRODUCTION: str = "production"
    DEVELOPMENT: str = "development"
    STAGE: str = "stage"
