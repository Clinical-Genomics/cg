from enum import StrEnum


class PacBioDirsAndFiles(StrEnum):
    ADAPTER_REPORT: str = "adapter.report.json"
    CCS_REPORT: str = "ccs.report.json"
    CONTROL_REPORT: str = "control.report.json"
    LOADING_REPORT: str = "loading.report.json"
    RAW_DATA_REPORT: str = "raw_data.report.json"
