from pathlib import Path

from pydantic import BaseModel, field_validator

from cg.constants.constants import GenomeVersion
from cg.constants.sample_sources import SourceType
from cg.utils.utils import replace_non_alphanumeric


class WorkflowParameters(BaseModel):
    input: Path
    outdir: Path


class NalloParameters(WorkflowParameters):
    """Model for Nallo parameters."""

    filter_variants_hgnc_ids: str


class RarediseaseParameters(WorkflowParameters):
    """Model for Raredisease parameters.
    Make sure to exclude None when serializing to make it readable for raredisease"""

    analysis_type: str
    gcnvcaller_model: Path | None
    ploidy_model: Path | None
    readcount_intervals: Path | None
    references_directory: Path
    sample_id_map: Path
    save_mapped_as_cram: bool
    skip_germlinecnvcaller: bool
    vcfanno_extra_resources: str
    vep_filters_scout_fmt: str
    verifybamid_svd_bed: Path
    verifybamid_svd_mu: Path
    verifybamid_svd_ud: Path


class RNAFusionParameters(WorkflowParameters):
    """RNAFUSION parameters."""


class TaxprofilerParameters(WorkflowParameters):
    """Taxprofiler parameters."""


class TomteParameters(WorkflowParameters):
    """Model for Tomte parameters."""

    gene_panel_clinical_filter: Path
    tissue: str
    genome: str = GenomeVersion.HG38

    @field_validator("tissue", mode="before")
    @classmethod
    def restrict_tissue_values(cls, tissue: str | None) -> str:
        if tissue:
            return replace_non_alphanumeric(string=tissue)
        else:
            return SourceType.UNKNOWN

    @field_validator("genome", mode="before")
    @classmethod
    def restrict_genome_values(cls, genome: str) -> str:
        if genome == GenomeVersion.HG38:
            return GenomeVersion.GRCh38.value
        elif genome == GenomeVersion.HG19:
            return GenomeVersion.GRCh37.value
