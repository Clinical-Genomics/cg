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


RAREDISEASE_PREDICTED_SEX_METRIC = "predicted_sex_sex_check"

RAREDISEASE_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "percent_duplicates": {"norm": "lt", "threshold": 20},
    "PCT_PF_UQ_READS_ALIGNED": {"norm": "gt", "threshold": 0.95},
    "MEDIAN_TARGET_COVERAGE": {"norm": "gt", "threshold": 25},
    "PCT_TARGET_BASES_10X": {"norm": "gt", "threshold": 0.95},
    "PCT_EXC_ADAPTER": {"norm": "lt", "threshold": 0.0005},
    RAREDISEASE_PREDICTED_SEX_METRIC: {"norm": "eq", "threshold": None},
    "gender": {"norm": "eq", "threshold": None},
}

RAREDISEASE_PARENT_PEDDY_METRIC_CONDITION: dict[str, dict[str, Any]] = {
    "parent_error_ped_check": {"norm": "eq", "threshold": "False"},
}

RNAFUSION_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "uniquely_mapped_percent": {"norm": "gt", "threshold": 60},
    "PCT_MRNA_BASES": {"norm": "gt", "threshold": 80},
    "PCT_RIBOSOMAL_BASES": {"norm": "lt", "threshold": 5},
    "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.7},
}

TOMTE_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "uniquely_mapped_percent": {"norm": "gt", "threshold": 60},
    "PCT_MRNA_BASES": {"norm": "gt", "threshold": 80},
    "PCT_RIBOSOMAL_BASES": {"norm": "lt", "threshold": 5},
    "pct_duplication": {"norm": "lt", "threshold": 70},
}


MULTIQC_NEXFLOW_CONFIG = """process {
    withName:'MULTIQC' {
        memory = { 1.GB * task.attempt }
        time   = { 4.h  * task.attempt }
        cpus = 2
        ext.args = ' --data-format json '
    }
}
"""

RAREDISEASE_COVERAGE_FILE_TAGS: list[str] = ["coverage", "d4"]
RAREDISEASE_COVERAGE_INTERVAL_TYPE: str = "genes"
RAREDISEASE_COVERAGE_THRESHOLD: int = 10
