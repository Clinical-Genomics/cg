from enum import IntEnum, StrEnum


class Slurm(StrEnum):
    PARTITION: str = "partition"


class SlurmProcessing(IntEnum):
    MAX_NODE_MEMORY: int = 180
