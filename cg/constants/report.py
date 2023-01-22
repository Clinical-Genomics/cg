# Delivery report constants

from cgmodels.cg.constants import Pipeline

from cg.constants import DataDelivery

BALSAMIC_REPORT_ACCREDITED_PANELS = ["gmsmyeloid"]

REPORT_SUPPORTED_PIPELINES = (Pipeline.MIP_DNA, Pipeline.BALSAMIC, Pipeline.BALSAMIC_UMI)
REPORT_SUPPORTED_DATA_DELIVERY = (
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.ANALYSIS_SCOUT,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.FASTQ_QC_ANALYSIS,
    DataDelivery.FASTQ_ANALYSIS_SCOUT,
    DataDelivery.SCOUT,
)

NA_FIELD = "N/A"
YES_FIELD = "Ja"
NO_FIELD = "Nej"
PRECISION = 2

REPORT_GENDER = {
    "unknown": "Okänd",
    "female": "Kvinna",
    "male": "Man",
}

BALSAMIC_ANALYSIS_TYPE = {
    "tumor_wgs": "Tumör-endast (helgenomsekvensering)",
    "tumor_normal_wgs": "Tumör/normal (helgenomsekvensering)",
    "tumor_panel": "Tumör-endast (panelsekvensering)",
    "tumor_normal_panel": "Tumör/normal (panelsekvensering)",
}

# Report required fields (OPTIONAL: "version")
REQUIRED_REPORT_FIELDS = [
    "customer",
    "date",
    "case",
    "accredited",
]

# Customer required fields (OPTIONAL: "id")
REQUIRED_CUSTOMER_FIELDS = [
    "name",
    "invoice_address",
    "scout_access",
]

# Case required fields
REQUIRED_CASE_FIELDS = [
    "name",
    "id",
    "samples",
    "data_analysis",
    "applications",
]

# Application required fields (OPTIONAL: "version", "prep_category", "description", "limitations", "external")
REQUIRED_APPLICATION_FIELDS = [
    "tag",
    "accredited",
]

# Data analysis required fields
_REQUIRED_DATA_ANALYSIS_FIELDS = [
    "customer_pipeline",
    "pipeline",
    "pipeline_version",
    "genome_build",
]

REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS = _REQUIRED_DATA_ANALYSIS_FIELDS + [
    "panels",
]

REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS = _REQUIRED_DATA_ANALYSIS_FIELDS + [
    "type",
    "variant_callers",
]

# Sample required fields
_REQUIRED_SAMPLE_FIELDS = [
    "name",
    "id",
    "ticket",
    "gender",
    "source",
    "application",
    "methods",
    "metadata",
    "timestamps",
]

REQUIRED_SAMPLE_MIP_DNA_FIELDS = _REQUIRED_SAMPLE_FIELDS + [
    "status",
]

REQUIRED_SAMPLE_BALSAMIC_FIELDS = _REQUIRED_SAMPLE_FIELDS + [
    "tumour",
]

# Methods required fields (OPTIONAL: "library_prep", "sequencing")
REQUIRED_SAMPLE_METHODS_FIELDS = []

# Timestamp required fields (OPTIONAL: "prepared_at", "sequenced_at")
REQUIRED_SAMPLE_TIMESTAMP_FIELDS = [
    "ordered_at",
    "received_at",  # Optional for external samples
]

# Metadata required fields
_REQUIRED_SAMPLE_METADATA_FIELDS = [
    "million_read_pairs",
    "duplicates",
]

REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "gender",
    "mapped_reads",
    "mean_target_coverage",
    "pct_10x",
]

REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS = REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS + [
    "bait_set",
]

_REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "mean_insert_size",
    "fold_80",
]

REQUIRED_SAMPLE_METADATA_BALSAMIC_TARGETED_FIELDS = _REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS + [
    "bait_set",
    "bait_set_version",
    "median_target_coverage",
    "pct_250x",
    "pct_500x",
]

REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS = _REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS + [
    "median_coverage",
    "pct_60x",
]

REQUIRED_SAMPLE_METADATA_BALSAMIC_TN_WGS_FIELDS = (
    REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS
    + [
        "pct_15x",
    ]
)
