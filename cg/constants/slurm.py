from enum import StrEnum


class Slurm(StrEnum):
    PARTITION: str = "partition"


SLURM_UPLOAD_MEMORY = 1
SLURM_UPLOAD_MAX_HOURS = 24
SLURM_UPLOAD_EXCLUDED_COMPUTE_NODES = "--exclude=gpu-compute-0-[0-1],cg-dragen"
SLURM_UPLOAD_TASKS = 1
