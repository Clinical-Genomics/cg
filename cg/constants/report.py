from cgmodels.cg.constants import Pipeline


REPORT_SUPPORTED_PIPELINES = (Pipeline.BALSAMIC, Pipeline.MIP_DNA)

REPORT_ACCREDITED_PANELS = ["gmsmyeloid"]

# Validation constants

PRECISION = 2
NA_FIELD = "N/A"
YES_FIELD = "Ja"
NO_FIELD = "Nej"

# Report required fields
REQUIRED_REPORT_FIELDS = [
    "customer",
    # "version",
    "date",
    "case",
    "accredited",
]

# Customer required fields

REQUIRED_CUSTOMER_FIELDS = [
    "name",
    # "id",
    "invoice_address",
    "scout_access",
]

# Case required fields
REQUIRED_CASE_FIELDS = [
    "name",
    "samples",
    "data_analysis",
    "applications",
]

# Application required fields

REQUIRED_APPLICATION_FIELDS = [
    "tag",
    # "version",
    # "prep_category",
    # "description",
    # "limitations",
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
    "timestamp",
]

REQUIRED_SAMPLE_MIP_DNA_FIELDS = _REQUIRED_SAMPLE_FIELDS + [
    "status",
]

REQUIRED_SAMPLE_BALSAMIC_FIELDS = _REQUIRED_SAMPLE_FIELDS + [
    "tumour",
]

# Methods required fields

REQUIRED_SAMPLE_METHODS_FIELDS = [
    # "library_prep",
    # "sequencing",
]

# Timestamp required fields
REQUIRED_SAMPLE_TIMESTAMPS_FIELDS = [
    "ordered_at",
    "received_at",
    # "prepared_at",
    # "sequenced_at",
    "delivered_at",
    "processing_days",
]

# Metadata required fields

_REQUIRED_SAMPLE_METADATA_FIELDS = [
    "million_read_pairs",
    "duplicates",
]

REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "bait_set",
    "gender",
    "mapped_reads",
    "mean_target_coverage",
    "pct_10x",
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

REQUIRED_SAMPLE_METADATA_BALSAMIC_WGS_FIELDS = _REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS + [
    "median_coverage",
    "pct_15x",
    "pct_60x",
]
