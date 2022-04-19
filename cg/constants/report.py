from cgmodels.cg.constants import Pipeline

# Validation constants
REPORT_SUPPORTED_PIPELINES = Pipeline.MIP_DNA
PRECISION = 2
NA_FIELD = "N/A"
YES_FIELD = "Ja"
NO_FIELD = "Nej"

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
    "samples",
    "data_analysis",
    "applications",
]

# Application required fields (OPTIONAL: "version", "prep_category", "description", "limitations")
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


# Methods required fields (OPTIONAL: "library_prep", "sequencing")
REQUIRED_SAMPLE_METHODS_FIELDS = []

# Timestamp required fields (OPTIONAL: "prepared_at", "sequenced_at")
REQUIRED_SAMPLE_TIMESTAMP_FIELDS = [
    "ordered_at",
    "received_at",
    "delivered_at",
    "processing_days",
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
