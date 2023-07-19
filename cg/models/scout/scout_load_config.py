"""Class to hold information about scout load config"""

from datetime import datetime
from typing import List, Optional

from pydantic.v1 import BaseModel, validator
from typing_extensions import Literal


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
    analysis_type: Literal[
        "external",
        "mixed",
        "panel",
        "panel-umi",
        "unknown",
        "wes",
        "wgs",
        "wts",
    ] = None
    capture_kit: Optional[str] = None
    confirmed_parent: Optional[bool] = None
    confirmed_sex: Optional[bool] = None
    father: Optional[str] = None
    mother: Optional[str] = None
    phenotype: Optional[str] = None
    sample_id: str = None
    sample_name: Optional[str] = None
    sex: Optional[str] = None
    subject_id: Optional[str] = None
    tissue_type: Optional[str] = None

    @validator("sample_id", "sex", "analysis_type")
    def field_not_none(cls, value):
        if value is None:
            raise ValueError("sample_id, sex and analysis_type can not be None")
        return value

    class Config:
        validate_assignment = True


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
    owner: str = None
    family: str = None
    family_name: Optional[str] = None
    synopsis: Optional[str] = None
    phenotype_terms: Optional[List[str]] = None
    phenotype_groups: Optional[List[str]] = None
    gene_panels: Optional[List[str]] = None
    default_gene_panels: List[str] = []
    cohorts: Optional[List[str]] = None
    human_genome_build: str = None

    rank_model_version: Optional[str] = None
    rank_score_threshold: int = None
    sv_rank_model_version: Optional[str] = None
    analysis_date: datetime = None
    samples: List[ScoutIndividual] = []

    delivery_report: Optional[str] = None
    coverage_qc_report: Optional[str] = None
    cnv_report: Optional[str] = None
    multiqc: Optional[str] = None
    track: Literal["rare", "cancer"] = "rare"

    @validator("owner", "family")
    def field_not_none(cls, value):
        if value is None:
            raise ValueError("Owner and family can not be None")
        return value

    class Config:
        validate_assignment = True


class BalsamicLoadConfig(ScoutLoadConfig):
    madeline: Optional[str]
    vcf_cancer: str = None
    vcf_cancer_sv: Optional[str] = None
    vcf_cancer_research: Optional[str] = None
    vcf_cancer_sv_research: Optional[str] = None
    samples: List[ScoutCancerIndividual] = []

    @validator("vcf_cancer")
    def check_mandatory_files(cls, vcf):
        if vcf is None:
            raise ValueError("Vcf can not be none")
        return vcf


class BalsamicUmiLoadConfig(BalsamicLoadConfig):
    pass


class MipLoadConfig(ScoutLoadConfig):
    chromograph_image_files: Optional[List[str]]
    chromograph_prefixes: Optional[List[str]]
    madeline: Optional[str] = None
    peddy_check: Optional[str] = None
    peddy_ped: Optional[str] = None
    peddy_sex: Optional[str] = None
    samples: List[ScoutMipIndividual] = []
    smn_tsv: Optional[str] = None
    variant_catalog: Optional[str] = None
    vcf_mei: Optional[str] = None
    vcf_mei_research: Optional[str] = None
    vcf_snv: str = None
    vcf_snv_research: Optional[str] = None
    vcf_str: Optional[str] = None
    vcf_sv: Optional[str] = None
    vcf_sv_research: Optional[str] = None

    @validator("vcf_snv", "vcf_sv", "vcf_snv_research", "vcf_sv_research")
    def check_mandatory_files(cls, vcf):
        if vcf is None:
            raise ValueError("Mandatory vcf can not be None")
        return vcf


class RnafusionLoadConfig(ScoutLoadConfig):
    multiqc_rna: Optional[str] = None
    gene_fusion: Optional[str] = None
    gene_fusion_report_research: Optional[str] = None
    RNAfusion_inspector: Optional[str] = None
    RNAfusion_inspector_research: Optional[str] = None
    RNAfusion_report: Optional[str] = None
    RNAfusion_report_research: Optional[str] = None
    samples: List[ScoutCancerIndividual] = []
