"""Nf-tower related constants."""

from enum import StrEnum
from typing import Any


class NfTowerStatus(StrEnum):
    """NF-Tower job submission status."""

    SUBMITTED: str = "SUBMITTED"
    RUNNING: str = "RUNNING"
    SUCCEEDED: str = "SUCCEEDED"
    FAILED: str = "FAILED"
    CANCELLED: str = "CANCELLED"
    UNKNOWN: str = "UNKNOWN"


RNAFUSION_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "uniquely_mapped_percent": {"norm": "gt", "threshold": 60},
    "PCT_MRNA_BASES": {"norm": "gt", "threshold": 80},
    "PCT_RIBOSOMAL_BASES": {"norm": "lt", "threshold": 5},
    "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.7},
}
