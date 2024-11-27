from enum import StrEnum

from cg.constants.sequencing import SeqLibraryPrepCategory


class AnalysisStatus:
    CANCELLED: str = "cancelled"
    COMPLETED: str = "completed"
    ERROR: str = "error"
    FAILED: str = "failed"
    PENDING: str = "pending"
    RUNNING: str = "running"
    TIMEOUT: str = "timeout"
    QC: str = "qc"


class AnalysisTypes(StrEnum):
    OTHER: str = "other"
    TGS: str = "tgs"
    WES: str = SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
    WGS: str = SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    WTS: str = SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING
