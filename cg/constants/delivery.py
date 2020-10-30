"""Constants for delivery"""
from pathlib import Path

PROJECT_BASE_PATH = Path("/home/proj/production/customers")

BALSAMIC_ANALYSIS_CASE_TAGS = [
    "clinical-vcf-pass",
    "clinical-vcf-pass-index",
    "cnv-gene-metrics",
    "cnv-scatter",
    "cnv-diagram",
    "multiqc-html",
    "tumor-bam",
    "tumor-cram",
    "normal-bam",
    "normal-cram",
]

BALSAMIC_ANALYSIS_SAMPLE_TAGS = ["bam", "bam-index", "cram", "cram-index"]

MIP_DNA_ANALYSIS_CASE_TAGS = [
    "vcf-clinical-sv-bin",
    "vcf-clinical-sv-bin-index",
    "vcf-research-sv-bin",
    "vcf-research-sv-bin-index",
    "gbcf",
    "gbcf-index",
    "snv-gbcf",
    "snv-gbcf-index",
    "snv-bcf",
    "snv-bcf-index",
    "sv-bcf",
    "sv-bcf-index",
    "vcf-snv-clinical",
    "vcf-snv-clinical-index",
    "vcf-snv-research",
    "vcf-snv-research-index",
    "vcf-sv-clinical",
    "vcf-sv-clinical-index",
    "vcf-sv-research",
    "vcf-sv-research-index",
]

MIP_DNA_ANALYSIS_SAMPLE_TAGS = ["bam", "bam-index", "cram", "cram-index"]

MIP_RNA_ANALYSIS_CASE_TAGS = []

MIP_RNA_ANALYSIS_SAMPLE_TAGS = ["bam", "bam-index", "cram", "cram-index"]

MICROSALT_ANALYSIS_CASE_TAGS = [
    "microsalt-qc",
    "microsalt-type",
    "assembly",
    "trimmed-forward-reads",
    "trimmed-reverse-reads",
    "reference-alignment-deduplicated",
]

MICROSALT_ANALYSIS_SAMPLE_TAGS = []

PIPELINE_ANALYSIS_TAG_MAP = {
    "balsamic": {
        "case_tags": BALSAMIC_ANALYSIS_CASE_TAGS,
        "sample_tags": BALSAMIC_ANALYSIS_SAMPLE_TAGS,
    },
    "mip-dna": {
        "case_tags": MIP_DNA_ANALYSIS_CASE_TAGS,
        "sample_tags": MIP_DNA_ANALYSIS_SAMPLE_TAGS,
    },
    "mip-rna": {
        "case_tags": MIP_RNA_ANALYSIS_CASE_TAGS,
        "sample_tags": MIP_RNA_ANALYSIS_SAMPLE_TAGS,
    },
    "microsalt": {
        "case_tags": MICROSALT_ANALYSIS_CASE_TAGS,
        "sample_tags": MICROSALT_ANALYSIS_SAMPLE_TAGS,
    },
}

PIPELINE_ANALYSIS_OPTIONS = PIPELINE_ANALYSIS_TAG_MAP.keys()
