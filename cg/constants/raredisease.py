"""Raredisease related constants."""

from typing import Any

RAREDISEASE_COVERAGE_FILE_TAGS: list[str] = ["coverage", "d4"]
RAREDISEASE_COVERAGE_INTERVAL_TYPE: str = "genes"
RAREDISEASE_COVERAGE_THRESHOLD: int = 10

RAREDISEASE_METRIC_CONDITIONS: dict[str, dict[str, Any]] = {
    "percent_duplicates": {"norm": "lt", "threshold": 20},
    "PCT_PF_UQ_READS_ALIGNED": {"norm": "gt", "threshold": 0.95},
    "MEDIAN_TARGET_COVERAGE": {"norm": "gt", "threshold": 26},
    "PCT_TARGET_BASES_10X": {"norm": "gt", "threshold": 0.95},
    "PCT_EXC_ADAPTER": {"norm": "lt", "threshold": 0.0005},
    "predicted_sex_sex_check": {"norm": "eq", "threshold": None},
}
