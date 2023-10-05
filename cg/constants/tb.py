from enum import Enum


class AnalysisStatus:
    CANCELLED: str = "cancelled"
    COMPLETED: str = "completed"
    ERROR: str = "error"
    FAILED: str = "failed"
    PENDING: str = "pending"
    RUNNING: str = "running"
    TIMEOUT: str = "timeout"
    QC: str = "qc"


class AnalysisTypes(str, Enum):
    WGS: str = "wgs"
    WES: str = "wes"
    TGS: str = "tgs"
    RNA: str = "rna"
    WTS: str = "wts"
    OTHER: str = "other"
