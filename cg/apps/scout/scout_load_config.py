"""Class to hold information about scout load config"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from typing_extensions import Literal


class ScoutIndividual(BaseModel):
    sample_id: str
    father: Optional[str] = None
    mother: Optional[str] = None
    sample_name: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    phenotype: Literal["affected", "unaffected", "unknown"]
    capture_kit: Optional[str] = None
    alignment_path: Optional[str] = None
    mt_bam: Optional[str] = None
    chromograph_images: Optional[dict] = None
    rhocall_bed: Optional[str] = None
    rhocall_wig: Optional[str] = None
    tiddit_coverage_wig: Optional[str] = None
    upd_regions_bed: Optional[str] = None
    upd_sites_bed: Optional[str] = None
    vcf2cytosure: Optional[str] = None
    analysis_type: Literal["wgs", "wes", "mixed", "unknown", "panel", "external"]
    confirmed_sex: Optional[bool] = None
    confirmed_parent: Optional[bool] = None
    is_sma: Optional[bool] = None
    is_sma_carrier: Optional[bool] = None
    smn1_cn: Optional[int] = None  # CopyNumber
    smn2_cn: Optional[int] = None  # CopyNumber
    smn2delta78_cn: Optional[int] = None  # CopyNumber
    smn_27134_cn: Optional[int] = None  # CopyNumber
    tumor_type: Optional[str] = None
    tmb: Optional[str] = None
    msi: Optional[str] = None
    tumor_purity: Optional[float] = None
    tissue_type: Optional[str] = None


class ScoutLoadConfig(BaseModel):
    owner: str
    family: str
    family_name: Optional[str] = None
    synopsis: Optional[str] = None
    phenotype_terms: Optional[List[str]] = None
    gene_panels: Optional[List[str]] = None
    default_gene_panels: List[str] = []
    cohorts: Optional[List[str]] = None
    human_genome_build: str
    madeline: Optional[str]
    rank_model_version: Optional[str] = None
    rank_score_threshold: int
    sv_rank_model_version: Optional[str] = None
    analysis_date: datetime
    samples: List[ScoutIndividual]
    vcf_snv_research: Optional[str] = None
    vcf_snv: Optional[str] = None
    vcf_sv: Optional[str] = None
    vcf_str: Optional[str] = None
    vcf_cancer: Optional[str] = None
    vcf_cancer_sv: Optional[str] = None
    vcf_sv_research: Optional[str] = None
    vcf_cancer_research: Optional[str] = None
    vcf_cancer_sv_research: Optional[str] = None
    smn_tsv: Optional[str] = None
    peddy_ped: Optional[str] = None
    peddy_sex: Optional[str] = None
    peddy_check: Optional[str] = None
    delivery_report: Optional[str] = None
    cnv_report: Optional[str] = None
    multiqc: Optional[str] = None
    track: Literal["rare", "cancer"] = "rare"
    chromograph_image_files: Optional[List[str]]
    chromograph_prefixes: Optional[List[str]]
