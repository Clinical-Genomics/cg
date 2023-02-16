"""File tags for files in Housekeeper."""
from enum import Enum
from typing import List

from cgmodels.cg.constants import Pipeline, StrEnum


class AlignmentFileTag(StrEnum):
    """Tags for alignment files."""

    BAM: str = "bam"
    BAM_BAI: str = "bai"
    BAM_INDEX: str = "bam-index"
    CRAM: str = "cram"
    CRAM_CRAI: str = "crai"
    CRAM_INDEX: str = "cram-index"


ALIGNMENT_FILE_TAGS: List[str] = [tag.value for tag in AlignmentFileTag]


class ArchiveTag(StrEnum):
    """Tags for archived status."""

    ARCHIVED: str = "archived"


class ScoutTag(StrEnum):
    """Tags for Scout."""

    ARCHIVED: str = "archived"
    SOLVED: str = "solved"


class SequencingFileTag(StrEnum):
    """Tags for sequencing files."""

    ARCHIVED_SAMPLE_SHEET: str = "archived_sample_sheet"
    CGSTATS_LOG: str = "log"
    FASTQ: str = "fastq"
    SAMPLE_SHEET: str = "samplesheet"
    SPRING: str = "spring"
    SPRING_METADATA: str = "spring-metadata"


HK_FASTQ_TAGS = [SequencingFileTag.FASTQ]

HK_DELIVERY_REPORT_TAG = "delivery-report"


class HkMipAnalysisTag:
    CONFIG: List[str] = ["mip-config"]
    QC_METRICS: List[str] = ["qc-metrics", "deliverable"]
    SAMPLE_INFO: List[str] = ["sample-info"]


class BalsamicAnalysisTag(StrEnum):
    CONFIG: str = "balsamic-config"
    QC_METRICS: str = "qc-metrics"


class GensAnalysisTag:
    COVERAGE: List[str] = ["gens", "coverage", "bed"]
    FRACSNP: List[str] = ["gens", "fracsnp", "bed"]


WORKFLOW_PROTECTED_TAGS = {
    str(Pipeline.BALSAMIC): [],
    str(Pipeline.FASTQ): [],
    str(Pipeline.FLUFFY): ["NIPT_csv", "MultiQC"],
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
        ["vcf-clinical"],  # legacy
        ["vcf-snv-research"],
        ["vcf-research"],  # legacy
        ["vcf-str"],
        ["snv-gbcf", "snv-bcf"],
        ["bcf-raw"],  # legacy
        ["bcf-raw-index"],  # legacy
        ["mip-config"],
        ["config"],  # legacy
        ["mip-log"],
        ["log"],  # legacy
        ["mip-analyse", "reference-info"],
        ["sample-info"],
        ["sampleinfo"],  # legacy
        ["qc-metrics"],
        ["qc"],  # legacy
        ["smn-calling"],
        ["sv-bcf"],
        ["bcf-raw-sv"],  # legacy
        ["vcf-sv-clinical"],
        ["vcf-clinical-sv"],  # legacy
        ["vcf-clinical-sv-bin"],  # legacy
        ["vcf-clinical-sv-bin-index"],  # legacy
        ["vcf-sv-research"],
        ["vcf-research-sv"],  # legacy
        ["vcf-research-sv-bin"],  # legacy
        ["vcf-research-sv-bin-index"],  # legacy
        ["exe-ver"],
        ["vcf2cytosure"],
        ["delivery-report"],
        ["madeline"],
        ["multiqc-html"],
        ["storage"],
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
