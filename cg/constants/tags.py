"""Tags for storing analyses in Housekeeper"""

from typing import List

HK_FASTQ_TAGS = ["fastq"]


class HkMipAnalysisTag:
    CONFIG: List[str] = ["mip-config"]
    QC_METRICS: List[str] = ["qc-metrics", "deliverables"]
    SAMPLE_INFO: List[str] = ["sample-info"]
