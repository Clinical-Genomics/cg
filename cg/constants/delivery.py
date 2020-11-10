"""Constants for delivery"""


BALSAMIC_ANALYSIS_CASE_TAGS = [
    {"cnv", "cnvkit", "vcf-all", "annotated-somatic-vcf-all"},
    {"cnv", "cnvkit", "vcf-all", "annotated-somatic-vcf-all-index"},
    {"vardict", "snv", "annotated-somatic-vcf-pass, vcf-pass"},
    {"vardict", "snv", "annotated-somatic-vcf-pass-index", "vcf-pass"},
    {"manta", "sv", "annotated-somatic-vcf-pass", "vcf-pass"},
    {"manta", "sv", "annotated-somatic-vcf-pass-index", "vcf-pass"},
    {"cnv-scatter"},
    {"cnv-diagram"},
    {"multiqc-html"},
    {"balsamic-report"},
    {"normal-cram"},
    {"normal-cram-index"},
    {"tumor-cram"},
    {"tumor-cram-index"},
]
BALSAMIC_ANALYSIS_SAMPLE_TAGS = []

BALSAMIC_QC_CASE_TAGS = [
    {"multiqc-html"},
]
BALSAMIC_QC_SAMPLE_TAGS = [
    {"quality-trimmed-fastq-read1"},  # also do the same if a normal sample exists
    {"quality-trimmed-fastq-read2"},  # also do the same if a normal sample exists
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
