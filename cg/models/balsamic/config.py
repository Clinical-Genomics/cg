import os.path
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Union, Optional

from pydantic import BaseModel, validator


class BalsamicConfigAnalysis(BaseModel):
    """Balsamic analysis model

    Attributes:
        case_id: case internal ID
        analysis_type: analysis type (single, paired or pon)
        sequencing_type: analysis sequencing type (wgs or targeted)
        BALSAMIC_version: BALSAMIC version used to produce the analysis
        config_creation_date: config creation timestamp
    """

    case_id: str
    analysis_type: str
    sequencing_type: str
    BALSAMIC_version: str
    config_creation_date: Union[datetime, str]


class BalsamicConfigSample(BaseModel):
    """Sample attributes used for BALSAMIC analysis

    Attributes:
        file_prefix: sample basename
        sample_name: sample internal ID
        type: sample type (tumor or normal)
    """

    file_prefix: str
    sample_name: str
    type: str


class BalsamicConfigReference(BaseModel):
    """Metadata of reference files

    Attributes:
        reference_genome: reference genome fasta file
        reference_genome_version: reference genome build version
        reference_access_date: date the reference was used for the analysis
    """

    reference_genome: Path
    reference_genome_version: Union[None, Path, str]
    reference_access_date: Union[datetime, Path]

    @validator("reference_genome_version", always=True)
    def validate_genome_version(cls, value: Path, values: dict) -> str:
        """
        Returns the genome version from the reference path:
        /home/proj/stage/cancer/balsamic_cache/X.X.X/hg19/genome/human_g1k_v37.fasta
        """

        return str(values["reference_genome"]).split("/")[-3]

    @validator("reference_access_date")
    def validate_reference_date(cls, value: Path) -> datetime:
        """Formats the reference date"""

        return datetime.strptime(os.path.basename(value), "%Y-%m-%d %H:%M:%S")


class BalsamicConfigPanel(BaseModel):
    """BALSAMIC attributes of a PANEL BED file if it's provided

    Attributes:
        capture_kit: string representation of a path to the PANEL BED file
        capture_kit_version: capture kit version
        chrom: list of chromosomes in PANEL BED
    """

    capture_kit: Path
    capture_kit_version: Optional[str]
    chrom: List[str]

    @validator("capture_kit_version", always=True)
    def validate_genome_version(cls, value: Path, values: dict) -> str:
        """
        Returns the panel bed version from the capture kit path:
        /home/proj/stage/cancer/reference/target_capture_bed/production/balsamic/gicfdna_3.1_hg19_design.bed
        """

        return os.path.basename(values["capture_kit"]).split("_")[-3]


class BalsamicConfigQC(BaseModel):
    """Config QC attributes

    Attributes:
        picard_rmdup: if the duplicates has been removed or not
        adapter: adapter sequence that has been trimmed
        quality_trim: whether quality trimming has been performed in the workflow
        adapter_trim: whether adapter trimming has been performed in the workflow
        umi_trim: whether UMI trimming has been performed in the workflow
        min_seq_length: minimum sequence length cutoff for reads
        umi_trim_length: UMI trimming length
    """

    picard_rmdup: bool
    adapter: Optional[str]
    quality_trim: bool
    adapter_trim: bool
    umi_trim: bool
    min_seq_length: Optional[str]
    umi_trim_length: Optional[str]


class BalsamicVarCaller(BaseModel):
    """Variant caller attributes model

    Attributes:
        mutation: if it addresses somatic or germline mutations
        type: called variant type (CNV, SV, SNV, etc.)
        analysis_type: analysis type supported by the variant caller (single, paired or pon)
        sequencing_type: sequencing type supported (wgs or targeted)
        workflow_solution: supported workflow (BALSAMIC, Sentieon, Sentieon_umi, etc.)
    """

    mutation: str
    type: str
    analysis_type: List[str]
    sequencing_type: List[str]
    workflow_solution: List[str]


class BalsamicConfigJSON(BaseModel):
    """Model for BALSAMIC analysis config validation

    Attributes:
        analysis: config analysis attributes
        samples: sample attributes associated to a specific case
        reference: BALSAMIC build reference
        panel: panel attributes (targeted analysis exclusively)
        umiworkflow: whether the UMI analysis was performed or not
    """

    analysis: BalsamicConfigAnalysis
    samples: Dict[str, BalsamicConfigSample]
    reference: BalsamicConfigReference
    panel: Optional[BalsamicConfigPanel]
    QC: BalsamicConfigQC
    vcf: Dict[str, BalsamicVarCaller]
    bioinfo_tools_version: Dict[str, List[str]]
    umiworkflow: bool
