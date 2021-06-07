"""Tags for storing analyses in Housekeeper"""

from cgmodels.cg.constants import StrEnum

HK_FASTQ_TAGS = ["fastq"]


class HkMipAnalysisTag(StrEnum):
    CONFIG: str = "mip-config"
    QC_METRICS: str = "qc-metrics"
    SAMPLE_INFO: str = "sample-info"
