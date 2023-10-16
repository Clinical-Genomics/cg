"""Class to hold information about scout load config"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing_extensions import Annotated, Literal

from cg.models.scout.validators import field_not_none


class ChromographImages(BaseModel):
    autozygous: Optional[str] = None
    coverage: Optional[str] = None
    upd_regions: Optional[str] = None
    upd_sites: Optional[str] = None


class Reviewer(BaseModel):
    alignment: Optional[str] = None
    alignment_index: Optional[str] = None
    vcf: Optional[str] = None
    catalog: Optional[str] = None


class ScoutIndividual(BaseModel):
    alignment_path: Optional[str] = None
    analysis_type: Annotated[
        Literal[
            "external",
            "mixed",
            "panel",
            "panel-umi",
            "unknown",
            "wes",
            "wgs",
            "wts",
        ],
        BeforeValidator(field_not_none),
    ] = None
    capture_kit: Optional[str] = None
    confirmed_parent: Optional[bool] = None
    confirmed_sex: Optional[bool] = None
    father: Optional[str] = None
    mother: Optional[str] = None
    phenotype: Optional[str] = None
    sample_id: Annotated[str, BeforeValidator(field_not_none)] = None
    sample_name: Optional[str] = None
    sex: Annotated[Optional[str], BeforeValidator(field_not_none)] = None
    subject_id: Optional[str] = None
    tissue_type: Optional[str] = None

    model_config = ConfigDict(validate_assignment=True)


class ScoutMipIndividual(ScoutIndividual):
    mt_bam: Optional[str] = None
    chromograph_images: ChromographImages = ChromographImages()
    reviewer: Reviewer = Reviewer()
    rhocall_bed: Optional[str] = None
    rhocall_wig: Optional[str] = None
    tiddit_coverage_wig: Optional[str] = None
    upd_regions_bed: Optional[str] = None
    upd_sites_bed: Optional[str] = None
    vcf2cytosure: Optional[str] = None
    mitodel_file: Optional[str] = None


class ScoutCancerIndividual(ScoutIndividual):
    tumor_type: Optional[str] = None
    tmb: Optional[str] = None
    msi: Optional[str] = None
    tumor_purity: float = 0
    vcf2cytosure: Optional[str] = None


class ScoutLoadConfig(BaseModel):
    owner: Annotated[str, BeforeValidator(field_not_none)] = None
    family: Annotated[str, BeforeValidator(field_not_none)] = None
    family_name: Optional[str] = None
    synopsis: Optional[str] = None
    phenotype_terms: Optional[list[str]] = None
    phenotype_groups: Optional[list[str]] = None
    gene_panels: Optional[list[str]] = None
    default_gene_panels: list[str] = []
    cohorts: Optional[list[str]] = None
    human_genome_build: str = None

    rank_model_version: Optional[str] = None
    rank_score_threshold: int = None
    sv_rank_model_version: Optional[str] = None
    analysis_date: Optional[datetime] = None
    samples: list[ScoutIndividual] = []

    delivery_report: Optional[str] = None
    coverage_qc_report: Optional[str] = None
    cnv_report: Optional[str] = None
    multiqc: Optional[str] = None
    track: Literal["rare", "cancer"] = "rare"

    model_config = ConfigDict(validate_assignment=True)


class BalsamicLoadConfig(ScoutLoadConfig):
    madeline: Optional[str] = None
    vcf_cancer: Annotated[str, BeforeValidator(field_not_none)] = None
    vcf_cancer_sv: Optional[str] = None
    vcf_cancer_research: Optional[str] = None
    vcf_cancer_sv_research: Optional[str] = None
    samples: list[ScoutCancerIndividual] = []


class BalsamicUmiLoadConfig(BalsamicLoadConfig):
    pass


class MipLoadConfig(ScoutLoadConfig):
    chromograph_image_files: Optional[list[str]] = None
    chromograph_prefixes: Optional[list[str]] = None
    madeline: Optional[str] = None
    peddy_check: Optional[str] = None
    peddy_ped: Optional[str] = None
    peddy_sex: Optional[str] = None
    samples: list[ScoutMipIndividual] = []
    smn_tsv: Optional[str] = None
    variant_catalog: Optional[str] = None
    vcf_mei: Optional[str] = None
    vcf_mei_research: Optional[str] = None
    vcf_snv: Annotated[str, BeforeValidator(field_not_none)] = None
    vcf_snv_research: Annotated[Optional[str], BeforeValidator(field_not_none)] = None
    vcf_str: Optional[str] = None
    vcf_sv: Annotated[Optional[str], BeforeValidator(field_not_none)] = None
    vcf_sv_research: Annotated[Optional[str], BeforeValidator(field_not_none)] = None


class RnafusionLoadConfig(ScoutLoadConfig):
    multiqc_rna: Optional[str] = None
    gene_fusion: Optional[str] = None
    gene_fusion_report_research: Optional[str] = None
    RNAfusion_inspector: Optional[str] = None
    RNAfusion_inspector_research: Optional[str] = None
    RNAfusion_report: Optional[str] = None
    RNAfusion_report_research: Optional[str] = None
    samples: list[ScoutCancerIndividual] = []
