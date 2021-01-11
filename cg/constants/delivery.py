"""Constants for delivery"""

import copy

BALSAMIC_ANALYSIS_ONLY_CASE_TAGS = [
    {"cnvkit", "sv-vcf", "tumor"},
    {"cnvkit", "sv-vcf-index", "tumor"},
    {"cnvkit", "regions"},
    {"vcf-snv-clinical", "vardict", "filtered"},
    {"vcf-snv-clinical-index", "vardict", "filtered"},
    {"vcf-snv-clinical", "scope", "filtered", "sention"},
    {"vcf-snv-clinical-index", "scope", "filtered", "sention"},
    {"vcf", "sention", "haplotype-caller", "filtered"},
    {"vcf-index", "sention", "haplotype-caller", "filtered"},
    {"vcf-sv-clinical", "manta", "filtered"},
    {"vcf-sv-clinical-index", "manta", "filtered"},
    {"cnvkit", "visualization"},
    {"cnvkit", "visualization", "diagram"},
    {"multiqc-html"},
]

BALSAMIC_ANALYSIS_CASE_TAGS = copy.deepcopy(BALSAMIC_ANALYSIS_ONLY_CASE_TAGS)
BALSAMIC_ANALYSIS_CASE_TAGS.extend(
    [
        {"cram", "normal"},
        {"cram-index"},
        {"cram", "tumor"},
        {"cram-index", "tumor"},
    ]
)

BALSAMIC_ANALYSIS_SAMPLE_TAGS = [
    {"cram", "normal"},
    {"cram-index"},
    {"cram", "tumor"},
    {"cram-index", "tumor"},
    {"bam"},
    {"bam-index"},
    {"fastq"},
]

BALSAMIC_QC_CASE_TAGS = [
    {"multiqc-html"},
]
BALSAMIC_QC_SAMPLE_TAGS = [
    {"fastq"},
]


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

MIP_RNA_ANALYSIS_CASE_TAGS = []

MIP_RNA_ANALYSIS_SAMPLE_TAGS = [
    {"bam"},
    {"bam-index"},
    {"cram"},
    {"cram-index"},
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

PIPELINE_ANALYSIS_TAG_MAP = {
    "balsamic": {
        "case_tags": BALSAMIC_ANALYSIS_CASE_TAGS,
        "sample_tags": BALSAMIC_ANALYSIS_SAMPLE_TAGS,
    },
    "balsamic-analysis": {"case_tags": BALSAMIC_ANALYSIS_ONLY_CASE_TAGS, "sample_tags": []},
    "balsamic-qc": {
        "case_tags": BALSAMIC_QC_CASE_TAGS,
        "sample_tags": BALSAMIC_QC_SAMPLE_TAGS,
    },
    "mip-dna": {
        "case_tags": MIP_DNA_ANALYSIS_CASE_TAGS,
        "sample_tags": MIP_DNA_ANALYSIS_SAMPLE_TAGS,
    },
    "mip-rna": {
        "case_tags": MIP_RNA_ANALYSIS_CASE_TAGS,
        "sample_tags": MIP_RNA_ANALYSIS_SAMPLE_TAGS,
    },
    # These are not ready yet, add when microsalt cases are stored in db
    # "microsalt": {
    #     "case_tags": MICROSALT_ANALYSIS_CASE_TAGS,
    #     "sample_tags": MICROSALT_ANALYSIS_SAMPLE_TAGS,
    # },
}

PIPELINE_ANALYSIS_OPTIONS = PIPELINE_ANALYSIS_TAG_MAP.keys()
