"""Nf-tower related constants."""
from cg.utils.enums import StrEnum


class NfTowerStatus(StrEnum):
    """NF-Tower job submission status."""

    SUBMITTED: str = "SUBMITTED"
    RUNNING: str = "RUNNING"
    SUCCEEDED: str = "SUCCEEDED"
    FAILED: str = "FAILED"
    CANCELLED: str = "CANCELLED"
    UNKNOWN: str = "UNKNOWN"
