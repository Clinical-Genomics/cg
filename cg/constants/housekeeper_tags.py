"""File tags for files in Housekeeper."""

from enum import StrEnum

from cg.constants.constants import Workflow


class AlignmentFileTag(StrEnum):
    """Tags for alignment files."""

    BAM: str = "bam"
    BAM_BAI: str = "bai"
    BAM_INDEX: str = "bam-index"
    CRAM: str = "cram"
    CRAM_CRAI: str = "crai"
    CRAM_INDEX: str = "cram-index"

    @classmethod
    def file_tags(cls) -> list[str]:
        return list(map(lambda tag: tag.value, cls))


class ArchiveTag(StrEnum):
    """Tags for archived status."""

    ARCHIVED: str = "archived"


class ScoutTag(StrEnum):
    """Tags for Scout."""

    ARCHIVED: str = "archived"
    SOLVED: str = "solved"


class SequencingFileTag(StrEnum):
    """Tags for sequencing files."""

    CGSTATS_LOG: str = "log"
    DEMUX_LOG: str = "log"
    FASTQ: str = "fastq"
    RUN_PARAMETERS: str = "run-parameters"
    SAMPLE_SHEET: str = "samplesheet"
    SPRING: str = "spring"
    SPRING_METADATA: str = "spring-metadata"


HK_MULTIQC_HTML_TAG = ["multiqc-html"]

HK_FASTQ_TAGS = [SequencingFileTag.FASTQ]

HK_DELIVERY_REPORT_TAG = "delivery-report"


class HermesFileTag(StrEnum):
    """Tags for hermes."""

    CLINICAL_DELIVERY: str = "clinical-delivery"
    LONG_TERM_STORAGE: str = "long-term-storage"


class AnalysisTag(StrEnum):
    """Tags for analysis files."""

    ARRIBA: str = "arriba"
    ARRIBA_VISUALIZATION: str = "arriba-visualisation"
    FUSION: str = "fusion"
    FUSIONCATCHER: str = "fusioncatcher"
    FUSIONCATCHER_SUMMARY: str = "fusioncatcher-summary"
    FUSIONINSPECTOR: str = "fusioninspector"
    FUSIONINSPECTOR_HTML: str = "fusioninspector-html"
    FUSIONREPORT: str = "fusionreport"
    GENE_COUNTS: str = "gene-counts"
    MULTIQC_HTML: str = "multiqc-html"
    RESEARCH: str = "research"
    RNA: str = "rna"
    STARFUSION: str = "star-fusion"
    VCF_FUSION: str = "vcf-fusion"


class HkMipAnalysisTag:
    CONFIG: list[str] = ["mip-config"]
    QC_METRICS: list[str] = ["qc-metrics", "deliverable"]
    SAMPLE_INFO: list[str] = ["sample-info"]


class BalsamicAnalysisTag:
    CONFIG: list[str] = ["balsamic-config"]
    QC_METRICS: list[str] = ["qc-metrics", "deliverable"]


class GensAnalysisTag:
    COVERAGE: list[str] = ["gens", "coverage", "bed"]
    FRACSNP: list[str] = ["gens", "fracsnp", "bed"]


class BalsamicProtectedTags:
    """Balsamic workflow protected tags by type."""

    QC: list[list[str]] = [
        ["balsamic-config"],
        ["balsamic-dag"],
        ["balsamic-report"],
        ["delivery-report"],
        ["multiqc-html"],
        ["multiqc-json"],
        ["qc-metrics"],
    ]
    VARIANT_CALLERS: list[list[str]] = [
        ["ascatngs"],
        ["visualization"],
        ["cnv-report"],
        ["cnvkit"],
        ["delly"],
        ["germline"],
        ["svdb"],
        ["tnscope"],
        ["tnscope-umi"],
        ["vardict"],
        ["vcf2cytosure"],
    ]


WORKFLOW_PROTECTED_TAGS = {
    Workflow.BALSAMIC: BalsamicProtectedTags.QC + BalsamicProtectedTags.VARIANT_CALLERS,
    Workflow.BALSAMIC_QC: BalsamicProtectedTags.QC,
    Workflow.BALSAMIC_PON: [],
    Workflow.BALSAMIC_UMI: BalsamicProtectedTags.QC + BalsamicProtectedTags.VARIANT_CALLERS,
    Workflow.FASTQ: [],
    Workflow.FLUFFY: ["NIPT_csv", "MultiQC"],
    Workflow.MICROSALT: [
        ["microsalt-log"],
        ["config"],
        ["qc-report", "visualization"],
        ["typing-report", "visualization"],
        ["typing-report", "qc-metrics"],
        ["microsalt-config"],
        ["assembly"],
    ],
    Workflow.MIP_DNA: [
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
    Workflow.MIP_RNA: [
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
    Workflow.MUTANT: [
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
    Workflow.RNAFUSION: [
        [AnalysisTag.FUSION, AnalysisTag.ARRIBA],
        [AnalysisTag.FUSION, AnalysisTag.STARFUSION],
        [AnalysisTag.FUSION, AnalysisTag.FUSIONCATCHER],
        [AnalysisTag.FUSIONINSPECTOR],
        [AnalysisTag.FUSIONREPORT, AnalysisTag.RESEARCH],
        [AnalysisTag.FUSIONINSPECTOR_HTML, AnalysisTag.RESEARCH],
        [AnalysisTag.ARRIBA_VISUALIZATION, AnalysisTag.RESEARCH],
        [AnalysisTag.MULTIQC_HTML, AnalysisTag.RNA],
        [HK_DELIVERY_REPORT_TAG],
        [AnalysisTag.VCF_FUSION],
        [AnalysisTag.GENE_COUNTS],
    ],
    Workflow.TAXPROFILER: [
        [HermesFileTag.LONG_TERM_STORAGE],
    ],
    Workflow.TOMTE: [
        [HermesFileTag.LONG_TERM_STORAGE],
    ],
}


class JanusTags:
    """Tags to communicate with the JanusAPI."""

    tags_to_retrieve: list[str] = ["qc-metrics", "janus"]
    multi_qc_file_tags: list[str] = [
        "picard-alignment",
        "picard-duplicates",
        "picard-hs",
        "picard-insert-size",
        "picard-wgs",
        "samtools-stats",
        "somalier",
        "picard-rnaseq",
        "fastp",
        "star",
        "general-stats",
    ]
