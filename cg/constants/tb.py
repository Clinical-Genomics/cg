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
    OTHER = "other"
    TGS = SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING
    WES = SeqLibraryPrepCategory.WHOLE_EXOME_SEQUENCING
    WGS = SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING
    WTS = SeqLibraryPrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING
