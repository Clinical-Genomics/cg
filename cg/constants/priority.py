"""Priority specific constants"""

from enum import IntEnum, StrEnum


class SlurmQos(StrEnum):
    MAINTENANCE = "maintenance"
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXPRESS = "express"


class TrailblazerPriority(StrEnum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    EXPRESS = "express"


class PriorityTerms(StrEnum):
    EXPRESS = "express"
    PRIORITY = "priority"
    RESEARCH = "research"
    STANDARD = "standard"
    CLINICAL_TRIALS = "clinical_trials"


class Priority(IntEnum):
    research = 0
    standard = 1
    clinical_trials = 2
    priority = 3
    express = 4

    @classmethod
    def priority_to_slurm_qos(cls) -> dict["Priority", SlurmQos]:
        return {
            Priority.research: SlurmQos.LOW,
            Priority.standard: SlurmQos.NORMAL,
            Priority.priority: SlurmQos.HIGH,
            Priority.express: SlurmQos.EXPRESS,
            Priority.clinical_trials: SlurmQos.NORMAL,
        }


class SlurmAccount(StrEnum):
    PRODUCTION = "production"
    DEVELOPMENT = "development"
    STAGE = "stage"
