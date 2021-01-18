"""Class to hold information about scout load config"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel
from typing_extensions import Literal

# Individual classes


class ChromographImages(BaseModel):
    autozyg: Optional[str] = None
    coverage: Optional[str] = None
    upd_regions: Optional[str] = None
    upd_sites: Optional[str] = None


class ScoutIndividual(BaseModel):
    sample_id: str
    father: Optional[str] = None
    mother: Optional[str] = None
    sample_name: Optional[str] = None
    sex: Literal["male", "female", "unknown"]
    phenotype: Literal["affected", "unaffected", "unknown"] = None
    capture_kit: Optional[str] = None
    alignment_path: Optional[str] = None
    analysis_type: Literal["wgs", "wes", "mixed", "unknown", "panel", "external"]
    confirmed_sex: Optional[bool] = False
    confirmed_parent: Optional[bool] = False

    tissue_type: Optional[str] = None


class ScoutMipIndividual(ScoutIndividual):
    mt_bam: Optional[str] = None
    chromograph_images: ChromographImages = None
    rhocall_bed: Optional[str] = None
    rhocall_wig: Optional[str] = None
    tiddit_coverage_wig: Optional[str] = None
    upd_regions_bed: Optional[str] = None
    upd_sites_bed: Optional[str] = None
    vcf2cytosure: Optional[str] = None


class ScoutBalsamicIndividual(ScoutIndividual):
    tumor_type: Optional[str] = None
    tmb: Optional[str] = None
    msi: Optional[str] = None
    tumor_purity: Optional[float] = None


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

    rank_model_version: Optional[str] = None
    rank_score_threshold: int = None
    sv_rank_model_version: Optional[str] = None
    analysis_date: datetime
    samples: List[ScoutIndividual]

    delivery_report: Optional[str] = None
    cnv_report: Optional[str] = None
    multiqc: Optional[str] = None
    track: Literal["rare", "cancer"] = "rare"

    class Config:
        validate_assignment = True


class BalsamicLoadConfig(ScoutLoadConfig):
    madeline: Optional[str]
    vcf_cancer: str = None
    vcf_cancer_sv: Optional[str] = None
    vcf_cancer_research: Optional[str] = None
    vcf_cancer_sv_research: Optional[str] = None


class MipLoadConfig(ScoutLoadConfig):
    smn_tsv: Optional[str] = None
    chromograph_image_files: Optional[List[str]]
    chromograph_prefixes: Optional[List[str]]
    vcf_snv: str = None
    vcf_sv: Optional[str] = None
    vcf_str: Optional[str] = None
    vcf_snv_research: Optional[str] = None
    vcf_sv_research: Optional[str] = None
    peddy_ped: Optional[str] = None
    peddy_sex: Optional[str] = None
    peddy_check: Optional[str] = None
