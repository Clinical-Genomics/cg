"""Constants for delivery"""

import copy

ONLY_ONE_CASE_PER_TICKET = [
    "fastq",
    "microsalt",
    "sarscov2",
]

SKIP_MISSING = [
    "fastq",
    "microsalt",
    "sarscov2",
]

BALSAMIC_ANALYSIS_CASE_TAGS = [
    {"multiqc-html"},
    {"metrics"},
    {"visualization"},
    {"coverage"},
    {"vcf-sv-clinical"},
    {"vcf-sv-clinical-index"},
    {"vcf-sv-research"},
    {"vcf-sv-research-index"},
    {"vcf-snv-clinical"},
    {"vcf-snv-clinical-index"},
    {"vcf-snv-research"},
    {"vcf-snv-research-index"},
    {"germline", "vcf"},
    {"germline", "vcf-index"},
    {"vcf2cytosure"},
]

BALSAMIC_ANALYSIS_SAMPLE_TAGS = [
    {"cram"},
    {"cram-index"},
]

BALSAMIC_QC_ANALYSIS_CASE_TAGS = [
    {"multiqc-html"},
]

BALSAMIC_QC_ANALYSIS_SAMPLE_TAGS = [
    {"qc-cram"},
    {"qc-cram-index"},
]

BALSAMIC_UMI_ANALYSIS_CASE_TAGS = [
    {"vcf-umi-snv-clinical"},
    {"vcf-umi-snv-clinical-index"},
    {"vcf-umi-snv-research"},
    {"vcf-umi-snv-research-index"},
]

BALSAMIC_UMI_ANALYSIS_CASE_TAGS.extend(BALSAMIC_ANALYSIS_CASE_TAGS)

BALSAMIC_UMI_ANALYSIS_SAMPLE_TAGS = [
    {"umi-cram"},
    {"umi-cram-index"},
]

BALSAMIC_UMI_ANALYSIS_SAMPLE_TAGS.extend(BALSAMIC_ANALYSIS_SAMPLE_TAGS)


MIP_DNA_ANALYSIS_CASE_TAGS = [
    {"vcf-clinical-sv-bin"},
    {"vcf-clinical-sv-bin-index"},
    {"vcf-research-sv-bin"},
    {"vcf-research-sv-bin-index"},
    {"gbcf"},
    {"gbcf-index"},
    {"snv-gbcf"},
    {"snv-gbcf-index"},
    {"snv-bcf"},
    {"snv-bcf-index"},
    {"sv-bcf"},
    {"sv-bcf-index"},
    {"vcf-snv-clinical"},
    {"vcf-snv-clinical-index"},
    {"vcf-snv-research"},
    {"vcf-snv-research-index"},
    {"vcf-sv-clinical"},
    {"vcf-sv-clinical-index"},
    {"vcf-sv-research"},
    {"vcf-sv-research-index"},
]

MIP_DNA_ANALYSIS_SAMPLE_TAGS = [{"bam"}, {"bam-index"}, {"cram"}, {"cram-index"}]

MIP_RNA_ANALYSIS_CASE_TAGS = [
    {"fusion", "clinical", "pdf"},
    {"fusion", "research", "pdf"},
    {"fusion", "vcf"},
    {"fusion", "vcf-index"},
    {"vcf-snv-clinical"},
    {"vcf-snv-clinical-index"},
    {"vcf-snv-research"},
    {"vcf-snv-research-index"},
]

MIP_RNA_ANALYSIS_SAMPLE_TAGS = [
    {"fusion", "star-fusion"},
    {"fusion", "arriba"},
    {"cram"},
    {"cram-index"},
    {"fusion", "vcf"},
    {"fusion", "vcf-index"},
    {"salmon-quant"},
]

MICROSALT_ANALYSIS_CASE_TAGS = [
    {"microsalt-qc"},
    {"microsalt-type"},
    {"assembly"},
    {"trimmed-forward-reads"},
    {"trimmed-reverse-reads"},
    {"reference-alignment-deduplicated"},
]

MICROSALT_ANALYSIS_SAMPLE_TAGS = []

FASTQ_ANALYSIS_CASE_TAGS = []

FASTQ_ANALYSIS_SAMPLE_TAGS = [
    {"fastq"},
]

SARSCOV2_ANALYSIS_CASE_TAGS = [
    {"pangolin"},
    {"ks-delivery"},
]

SARSCOV2_ANALYSIS_SAMPLE_TAGS = [
    {"fastq"},
]

PIPELINE_ANALYSIS_TAG_MAP = {
    "balsamic": {
        "case_tags": BALSAMIC_ANALYSIS_CASE_TAGS,
        "sample_tags": BALSAMIC_ANALYSIS_SAMPLE_TAGS,
    },
    "balsamic-qc": {
        "case_tags": BALSAMIC_QC_ANALYSIS_CASE_TAGS,
        "sample_tags": BALSAMIC_QC_ANALYSIS_SAMPLE_TAGS,
    },
    "balsamic-umi": {
        "case_tags": BALSAMIC_UMI_ANALYSIS_CASE_TAGS,
        "sample_tags": BALSAMIC_UMI_ANALYSIS_SAMPLE_TAGS,
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
    "fastq": {
        "case_tags": FASTQ_ANALYSIS_CASE_TAGS,
        "sample_tags": FASTQ_ANALYSIS_SAMPLE_TAGS,
    },
    "sarscov2": {
        "case_tags": SARSCOV2_ANALYSIS_CASE_TAGS,
        "sample_tags": SARSCOV2_ANALYSIS_SAMPLE_TAGS,
    },
}

PIPELINE_ANALYSIS_OPTIONS = PIPELINE_ANALYSIS_TAG_MAP.keys()
