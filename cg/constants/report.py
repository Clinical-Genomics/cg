"""Delivery report constants."""

from pathlib import Path

from cg.constants import DataDelivery
from cg.constants.constants import CancerAnalysisType, FileExtensions, Workflow
from cg.constants.subject import Sex
from cg.utils.files import get_project_root_dir

project_root_dir: Path = get_project_root_dir()

DELIVERY_REPORT_FILE_NAME: str = f"delivery-report{FileExtensions.HTML}"
SWEDAC_LOGO_PATH = Path(
    project_root_dir, "meta", "delivery_report", "templates", "static", "images", "SWEDAC_logo.png"
)

BALSAMIC_REPORT_ACCREDITED_PANELS: list[str] = ["gmsmyeloid"]

RNAFUSION_REPORT_ACCREDITED_APPTAGS: list[str] = ["RNAPOAR100"]
RNAFUSION_REPORT_MINIMUM_INPUT_AMOUNT: int = 300

REPORT_SUPPORTED_WORKFLOW: tuple[Workflow, ...] = (
    Workflow.BALSAMIC,
    Workflow.BALSAMIC_UMI,
    Workflow.MIP_DNA,
    Workflow.NALLO,
    Workflow.RAREDISEASE,
    Workflow.RNAFUSION,
    Workflow.TAXPROFILER,
    Workflow.TOMTE,
)

REPORT_SUPPORTED_DATA_DELIVERY: tuple[DataDelivery, ...] = (
    DataDelivery.ANALYSIS_FILES,
    DataDelivery.ANALYSIS_SCOUT,
    DataDelivery.FASTQ_ANALYSIS,
    DataDelivery.FASTQ_ANALYSIS_SCOUT,
    DataDelivery.FASTQ_QC_ANALYSIS,
    DataDelivery.FASTQ_SCOUT,
    DataDelivery.RAW_DATA_ANALYSIS,
    DataDelivery.RAW_DATA_ANALYSIS_SCOUT,
    DataDelivery.RAW_DATA_SCOUT,
    DataDelivery.SCOUT,
)

NA_FIELD: str = "N/A"
YES_FIELD: str = "Ja"
NO_FIELD: str = "Nej"
PRECISION: int = 2

RIN_MAX_THRESHOLD: int = 10
RIN_MIN_THRESHOLD: int = 1

REPORT_SEX: dict[str, str] = {
    Sex.FEMALE: "Kvinna",
    Sex.MALE: "Man",
    Sex.UNKNOWN: "Okänd",
}

BALSAMIC_ANALYSIS_TYPE: dict[str, str] = {
    CancerAnalysisType.TUMOR_NORMAL_PANEL: "Tumör/normal (panelsekvensering)",
    CancerAnalysisType.TUMOR_NORMAL_WGS: "Tumör/normal (helgenomsekvensering)",
    CancerAnalysisType.TUMOR_PANEL: "Tumör-endast (panelsekvensering)",
    CancerAnalysisType.TUMOR_WGS: "Tumör-endast (helgenomsekvensering)",
}

REPORT_QC_FLAG: dict[bool | None, str] = {
    False: "Underkänd",
    True: "Godkänd",
    None: "Okänd",
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

REQUIRED_DATA_ANALYSIS_RAREDISEASE_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS + [
    "panels",
]

REQUIRED_DATA_ANALYSIS_MIP_DNA_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_RAREDISEASE_FIELDS

REQUIRED_DATA_ANALYSIS_NALLO_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS + [
    "panels",
]

REQUIRED_DATA_ANALYSIS_BALSAMIC_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS + [
    "type",
    "variant_callers",
]

REQUIRED_DATA_ANALYSIS_RNAFUSION_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS

REQUIRED_DATA_ANALYSIS_TAXPROFILER_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS

REQUIRED_DATA_ANALYSIS_TOMTE_FIELDS: list[str] = REQUIRED_DATA_ANALYSIS_FIELDS

# Sample required fields
_REQUIRED_SAMPLE_FIELDS: list[str] = [
    "name",
    "id",
    "ticket",
    "sex",
    "source",
    "application",
    "methods",
    "metadata",
    "timestamps",
]

REQUIRED_SAMPLE_RAREDISEASE_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS + [
    "status",
]

_REQUIRED_SAMPLE_CANCER_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS + [
    "tumour",
]

REQUIRED_SAMPLE_MIP_DNA_FIELDS: list[str] = REQUIRED_SAMPLE_RAREDISEASE_FIELDS

REQUIRED_SAMPLE_NALLO_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS + [
    "status",
]

REQUIRED_SAMPLE_BALSAMIC_FIELDS: list[str] = _REQUIRED_SAMPLE_CANCER_FIELDS

REQUIRED_SAMPLE_RNAFUSION_FIELDS: list[str] = _REQUIRED_SAMPLE_CANCER_FIELDS

REQUIRED_SAMPLE_TAXPROFILER_FIELDS: list[str] = _REQUIRED_SAMPLE_FIELDS

REQUIRED_SAMPLE_TOMTE_FIELDS: list[str] = REQUIRED_SAMPLE_RAREDISEASE_FIELDS

# Methods required fields (OPTIONAL: "library_prep", "sequencing")
REQUIRED_SAMPLE_METHODS_FIELDS: list[str] = []

# Timestamp required fields (OPTIONAL: "prepared_at", "reads_updated_at")
REQUIRED_SAMPLE_TIMESTAMP_FIELDS: list[str] = [
    "ordered_at",
    "received_at",  # Optional for external samples
]

# Metadata required fields
_REQUIRED_SAMPLE_METADATA_FIELDS: list[str] = [
    "duplicates",
    "initial_qc",
    "million_read_pairs",
]

REQUIRED_SAMPLE_METADATA_RAREDISEASE_WGS_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "sex",
    "mapped_reads",
    "mean_target_coverage",
    "pct_10x",
]

REQUIRED_SAMPLE_METADATA_RAREDISEASE_FIELDS: list[str] = (
    REQUIRED_SAMPLE_METADATA_RAREDISEASE_WGS_FIELDS
    + [
        "bait_set",
    ]
)

REQUIRED_SAMPLE_METADATA_MIP_DNA_WGS_FIELDS: list[str] = (
    REQUIRED_SAMPLE_METADATA_RAREDISEASE_WGS_FIELDS
)

REQUIRED_SAMPLE_METADATA_MIP_DNA_FIELDS: list[str] = REQUIRED_SAMPLE_METADATA_RAREDISEASE_FIELDS

REQUIRED_SAMPLE_METADATA_NALLO_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "mapped_reads",
    "mean_target_coverage",
    "pct_10x",
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

_REQUIRED_SAMPLE_METADATA_SEQUENCING_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_FIELDS + [
    "gc_content",
    "mean_length_r1",
]

# WHOLE_TRANSCRIPTOME_SEQUENCING metadata required fields (OPTIONAL: "rin", "dv200")
_REQUIRED_SAMPLE_METADATA_WTS_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_SEQUENCING_FIELDS + [
    "bias_5_3",
    "input_amount",
    "mrna_bases",
    "pct_adapter",
    "pct_surviving",
    "q20_rate",
    "q30_rate",
    "ribosomal_bases",
    "uniquely_mapped_reads",
]

REQUIRED_SAMPLE_METADATA_RNAFUSION_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_WTS_FIELDS + [
    "mapped_reads",
]


REQUIRED_SAMPLE_METADATA_TAXPROFILER_FIELDS: list[str] = []


REQUIRED_SAMPLE_METADATA_TOMTE_FIELDS: list[str] = _REQUIRED_SAMPLE_METADATA_WTS_FIELDS + [
    "pct_intergenic_bases",
    "pct_intronic_bases",
]
