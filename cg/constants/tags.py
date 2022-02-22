"""Tags for storing analyses in Housekeeper"""

from cgmodels.cg.constants import StrEnum, Pipeline

HK_FASTQ_TAGS = ["fastq"]


class HkMipAnalysisTag(StrEnum):
    CONFIG: str = "mip-config"
    QC_METRICS: str = "qc-metrics"
    SAMPLE_INFO: str = "sample-info"


WORKFLOW_PROTECTED_TAGS = {
    str(Pipeline.BALSAMIC): [],
    str(Pipeline.FASTQ): [],
    str(Pipeline.FLUFFY): [],
    str(Pipeline.MICROSALT): [
        ["microsalt-log"],
        ["config"],
        ["qc-report", "visualization"],
        ["typing-report", "visualization"],
        ["typing-report", "qc-metrics"],
        ["microsalt-config"],
        ["assembly"],
    ],
    str(Pipeline.MIP_DNA): [
        ["vcf-snv-clinical"],
        ["vcf-snv-research"],
        ["vcf-str"],
        ["snv-gbcf", "snv-bcf"],
        ["mip-config"],
        ["mip-log"],
        ["mip-analyse", "reference-info"],
        ["sample-info"],
        ["qc-metrics"],
        ["smn-calling"],
        ["sv-bcf"],
        ["vcf-sv-clinical"],
        ["vcf-sv-research"],
        ["exe-ver"],
        ["vcf2cytosure"],
    ],
    str(Pipeline.MIP_RNA): [
        ["vcf-snv-clinical"],
        ["vcf-snv-research"],
        ["mip-config"],
        ["mip-log"],
        ["mip-analyse, reference-info"],
        ["sample-info"],
        ["qc-metrics"],
        ["exe-ver"],
        ["fusion", "vcf"],
        ["salmon-quant"],
    ],
    str(Pipeline.SARS_COV_2): [
        ["fohm-delivery", "instrument-properties"],
        ["fohm-delivery", "pangolin-typing-fohm", "csv"],
        ["vcf", "vcf-report", "fohm-delivery"],
        ["mutant-log"],
        ["metrics"],
        ["config"],
        ["mutant-config"],
        ["software-versions"],
        ["fohm-delivery", "komplettering", "visualization"],
        ["fohm-delivery", "pangolin-typing", "csv", "visualization"],
        ["ks-delivery", "ks-results", "typing-report", "visualization", "csv"],
        ["ks-delivery", "ks-aux-results", "typing-report", "visualization", "csv"],
        ["multiqc-json"],
        ["gisaid-log"],
        ["gisaid-csv"],
    ],
}
