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


NALLO_GENERAL_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "median_coverage": {"norm": "gt", "threshold": 20},
}

NALLO_PARENT_PEDDY_METRIC_CONDITION: dict[str, dict[str, Any]] = {
    "parent_error_ped_check": {"norm": "eq", "threshold": "False"},
}

NALLO_RAW_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "somalier_sex": {"norm": "eq", "threshold": None},
}

RAREDISEASE_PREDICTED_SEX_METRIC = "predicted_sex_sex_check"

RAREDISEASE_METRIC_CONDITIONS_WES: dict[str, dict[str, Any]] = {
    "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.20},
    "PCT_PF_UQ_READS_ALIGNED": {"norm": "gt", "threshold": 0.95},
    "PCT_TARGET_BASES_10X": {"norm": "gt", "threshold": 0.95},
    "AT_DROPOUT": {"norm": "lt", "threshold": 10},
    "GC_DROPOUT": {"norm": "lt", "threshold": 10},
    RAREDISEASE_PREDICTED_SEX_METRIC: {"norm": "eq", "threshold": None},
    "gender": {"norm": "eq", "threshold": None},
}

RAREDISEASE_METRIC_CONDITIONS_WGS: dict[str, dict[str, Any]] = {
    "PERCENT_DUPLICATION": {"norm": "lt", "threshold": 0.20},
    "PCT_PF_UQ_READS_ALIGNED": {"norm": "gt", "threshold": 0.95},
    "MEDIAN_TARGET_COVERAGE": {"norm": "gt", "threshold": 25},
    "PCT_TARGET_BASES_10X": {"norm": "gt", "threshold": 0.95},
    "AT_DROPOUT": {"norm": "lt", "threshold": 5},
    "GC_DROPOUT": {"norm": "lt", "threshold": 5},
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
        memory = { 4.GB * task.attempt }
        time   = { 4.h  * task.attempt }
        cpus = 2
        ext.args = ' --data-format json --cl-config "max_table_rows: 10000" '
    }
}
"""

NALLO_COVERAGE_FILE_TAGS: list[str] = ["d4"]
NALLO_COVERAGE_INTERVAL_TYPE: str = "genes"
NALLO_COVERAGE_THRESHOLD: int = 10

RAREDISEASE_COVERAGE_FILE_TAGS: list[str] = ["coverage", "d4"]
RAREDISEASE_COVERAGE_INTERVAL_TYPE: str = "genes"
RAREDISEASE_COVERAGE_THRESHOLD: int = 10
