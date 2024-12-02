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


class AnalysisType(StrEnum):
    OTHER: str = "other"
    TGS: str = SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING
    WES: str = SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
    WGS: str = SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    WTS: str = SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING
