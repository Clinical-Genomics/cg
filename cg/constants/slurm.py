from enum import Enum

from cg.utils.enums import StrEnum


class Slurm(Enum):
    PARTITION: str = "partition"
    MAX_NODE_MEMORY: int = 180


class ContextEnv:
    STAGE: str = "stage"
    PRODUCTION: str = "production"


class SlurmAccount:
    DEV: str = "development"
    PROD: str = "production"


ENV_TO_SLURM_ACCOUNT = {
    ContextEnv.PRODUCTION: SlurmAccount.PROD,
    ContextEnv.STAGE: SlurmAccount.DEV,
}
