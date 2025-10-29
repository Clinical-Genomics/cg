from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from cg.constants.constants import SampleType


class BalsamicConfigAnalysis(BaseModel):
    """Balsamic analysis model

    Attributes:
        case_id: case internal ID
        analysis_type: analysis type (single, paired or pon)
        analysis_workflow: analysis carried out (balsamic or balsamic-umi)
        sequencing_type: analysis sequencing type (wgs or targeted)
        BALSAMIC_version: BALSAMIC version used to produce the analysis
        config_creation_date: config creation timestamp
    """

    case_id: str
    analysis_type: str
    analysis_workflow: str
    sequencing_type: str
    BALSAMIC_version: str
    config_creation_date: datetime | str


class BalsamicConfigSample(BaseModel):
    """Sample attributes used for Balsamic analysis.

    Attributes:
        type (str): sample type (tumor or normal)
    """

    type: SampleType
    name: str
    fastq_info: dict[str, dict[str, Path]]


class BalsamicConfigPanel(BaseModel):
    """Balsamic attributes of a panel BED file.

    Attributes:
        capture_kit: string representation of a panel BED filename
        capture_kit_version: capture kit version
        chrom: list of chromosomes in the panel BED file
        pon_cnn: panel of normal name and version applied to the CNVkit variant calling
    """

    capture_kit: str
    capture_kit_version: str | None = Field(default=None, validate_default=True)
    chrom: list[str]
    pon_cnn: str | None = None

    @field_validator("capture_kit", mode="before")
    @classmethod
    def get_filename_from_path(cls, path: str) -> str:
        """Return the base name of the provided file path."""
        return Path(path).name

    @field_validator("capture_kit_version")
    @classmethod
    def get_panel_version_from_filename(cls, _, info: ValidationInfo) -> str:
        """Return the panel bed version from its filename (e.g. gicfdna_3.1_hg19_design.bed)."""
        return info.data.get("capture_kit").split("_")[-3]

    @field_validator("pon_cnn", mode="before")
    @classmethod
    def get_pon_cnn_name_version_from_filename(cls, pon_cnn: str | None) -> str:
        """Return the CNVkit PON name and version from its filename (gmsmyeloid_5.3_hg19_design_CNVkit_PON_reference_v1.cnn)."""
        pon_cnn_filename_split: list[str] = Path(pon_cnn).stem.split("_")
        pon_cnn_name: str = f"{pon_cnn_filename_split[0]} v{pon_cnn_filename_split[1]}"
        pon_cnn_version: str = pon_cnn_filename_split[-1]
        pon_tool_name: str = pon_cnn_filename_split[4]
        return f"{pon_tool_name} {pon_cnn_name} ({pon_cnn_version})"


class BalsamicConfigQC(BaseModel):
    """Config QC attributes.

    Attributes:
        adapter: adapter sequence that has been trimmed
        min_seq_length: minimum sequence length cutoff for reads
    """

    adapter: str | None
    min_seq_length: str | None


class BalsamicVarCaller(BaseModel):
    """Variant caller attributes model.

    Attributes:
        mutation: if it addresses somatic or germline mutations
        type: called variant type (CNV, SV, SNV, etc.)
        analysis_type: analysis type supported by the variant caller (single, paired or pon)
        sequencing_type: sequencing type supported (wgs or targeted)
        workflow_solution: supported workflow (BALSAMIC, Sentieon, Sentieon_umi, etc.)
    """

    mutation: str
    mutation_type: str
    analysis_type: list[str]
    sequencing_type: list[str]
    workflow_solution: list[str]


class BalsamicConfigJSON(BaseModel):
    """Model for BALSAMIC analysis config validation.

    Attributes:
        analysis: config analysis attributes
        samples: sample attributes associated to a specific case
        panel: panel attributes (targeted analysis exclusively)
    """

    analysis: BalsamicConfigAnalysis
    samples: list[BalsamicConfigSample]
    panel: BalsamicConfigPanel | None = None
    QC: BalsamicConfigQC
    vcf: dict[str, BalsamicVarCaller]
    bioinfo_tools_version: dict[str, list[str]]
