"""Priority specific constants"""
from cgmodels.cg.constants import StrEnum

PRIORITY_MAP = {"research": 0, "standard": 1, "priority": 2, "express": 3, "clinical trials": 4}

REV_PRIORITY_MAP = {value: key for key, value in PRIORITY_MAP.items()}

PRIORITY_OPTIONS = list(PRIORITY_MAP.keys())


class SlurmQos(StrEnum):
    LOW: str = "low"
    NORMAL: str = "normal"
    HIGH: str = "high"
