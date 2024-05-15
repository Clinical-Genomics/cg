"""Delivery report constants."""

from cg.constants import DataDelivery
from cg.constants.constants import Workflow

BALSAMIC_REPORT_ACCREDITED_PANELS: list[str] = ["gmsmyeloid"]

REPORT_SUPPORTED_WORKFLOW: tuple[Workflow, ...] = (
    Workflow.BALSAMIC,
    Workflow.BALSAMIC_UMI,
    Workflow.BALSAMIC_QC,
    Workflow.MIP_DNA,
    Workflow.RNAFUSION,
)

REPORT_SUPPORTED_DATA_DELIVERY: tuple[DataDelivery, ...] = (
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.ANALYSIS_SCOUT,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.FASTQ_ANALYSIS_SCOUT,
    DataDelivery.FASTQ_QC_ANALYSIS,
    DataDelivery.FASTQ_SCOUT,
    DataDelivery.SCOUT,
)

NA_FIELD: str = "N/A"
YES_FIELD: str = "Ja"
NO_FIELD: str = "Nej"
PRECISION: int = 2

REPORT_GENDER: dict[str, str] = {
    "unknown": "Okänd",
    "female": "Kvinna",
    "male": "Man",
}

BALSAMIC_ANALYSIS_TYPE: dict[str, str] = {
    "tumor_wgs": "Tumör-endast (helgenomsekvensering)",
    "tumor_normal_wgs": "Tumör/normal (helgenomsekvensering)",
    "tumor_panel": "Tumör-endast (panelsekvensering)",
    "tumor_normal_panel": "Tumör/normal (panelsekvensering)",
}

# Report required fields (OPTIONAL: "version")
REQUIRED_REPORT_FIELDS: list[str] = [
    "customer",
    "date",
    "case",
    "accredited",
]

# Customer required fields (OPTIONAL: "id")
REQUIRED_CUSTOMER_FIELDS: list[str] = [
    "name",
    "invoice_address",
    "scout_access",
]

# Case required fields
REQUIRED_CASE_FIELDS: list[str] = [
    "name",
    "id",
    "samples",
    "data_analysis",
    "applications",
]

# Application required fields (OPTIONAL: "version", "prep_category", "description", "limitations", "external")
REQUIRED_APPLICATION_FIELDS: list[str] = [
    "tag",
    "accredited",
]

# Data analysis required fields
REQUIRED_DATA_ANALYSIS_FIELDS: list[str] = [
    "customer_workflow",
    "workflow",
    "workflow_version",
    "genome_build",
]

REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS + [
    "panels",
]

REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS + [
    "type",
    "variant_callers",
]

REQUIRED_DATA_ANALYSIS_RNAFUSION_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS

# Sample required fields
_REQUIRED_SAMPLE_FIELDS: list[str] = [
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

REQUIRED_SAMPLE_MIP_DNA_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS + [
    "status",
]

REQUIRED_SAMPLE_BALSAMIC_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS + [
    "tumour",
]

REQUIRED_SAMPLE_RNAFUSION_FIELDS: list[str] = REQUIRED_SAMPLE_BALSAMIC_FIELDS

# Methods required fields (OPTIONAL: "library_prep", "sequencing")
REQUIRED_SAMPLE_METHODS_FIELDS: list[str] = []

# Timestamp required fields (OPTIONAL: "prepared_at", "reads_updated_at")
REQUIRED_SAMPLE_TIMESTAMP_FIELDS: list[str] = [
    "ordered_at",
    "received_at",  # Optional for external samples
]

# Metadata required fields
_REQUIRED_SAMPLE_METADATA_FIELDS: list[str] = [
    "million_read_pairs",
    "duplicates",
]

REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "gender",
    "mapped_reads",
    "mean_target_coverage",
    "pct_10x",
]

REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS: list[str] = REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS + [
    "bait_set",
]

_REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "mean_insert_size",
    "fold_80",
]

REQUIRED_SAMPLE_METADATA_BALSAMIC_TARGETED_FIELDS: list[str] = (
    _REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS
    + [
        "bait_set",
        "bait_set_version",
        "median_target_coverage",
        "pct_250x",
        "pct_500x",
        "gc_dropout",
    ]
)

REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS: list[str] = (
    _REQUIRED_SAMPLE_METADATA_BALSAMIC_FIELDS
    + [
        "median_coverage",
        "pct_60x",
        "pct_reads_improper_pairs",
    ]
)

REQUIRED_SAMPLE_METADATA_BALSAMIC_TN_WGS_FIELDS: list[str] = (
    REQUIRED_SAMPLE_METADATA_BALSAMIC_TO_WGS_FIELDS
    + [
        "pct_15x",
    ]
)

REQUIRED_SAMPLE_METADATA_RNAFUSION_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "bias_5_3",
    "gc_content",
    "input_amount",
    "mapped_reads",
    "mean_length_r1",
    "mrna_bases",
    "pct_adapter",
    "pct_surviving",
    "q20_rate",
    "q30_rate",
    "ribosomal_bases",
    "rin",
    "uniquely_mapped_reads",
]
