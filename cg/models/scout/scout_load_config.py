"""Class to hold information about scout load config"""

from datetime import datetime

from pydantic import BaseModel, BeforeValidator, ConfigDict
from typing_extensions import Annotated, Literal

from cg.constants.scout import UploadTrack
from cg.models.scout.validators import field_not_none


class ChromographImages(BaseModel):
    autozygous: str | None = None
    coverage: str | None = None
    upd_regions: str | None = None
    upd_sites: str | None = None


class Eklipse(BaseModel):
    title: str | None = None
    description: str | None = None
    width: str | None = None
    height: str | None = None
    path: str | None = None


class CaseImages(BaseModel):
    eKLIPse: list[Eklipse] | None = None


class CustomImages(BaseModel):
    case_images: CaseImages | None = None


class Reviewer(BaseModel):
    alignment: str | None = None
    alignment_index: str | None = None
    vcf: str | None = None
    catalog: str | None = None


class ScoutIndividual(BaseModel):
    alignment_path: str | None = None
    rna_alignment_path: str | None = None
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
    capture_kit: str | None = None
    confirmed_parent: bool | None = None
    confirmed_sex: bool | None = None
    father: str | None = None
    mother: str | None = None
    phenotype: str | None = None
    sample_id: Annotated[str, BeforeValidator(field_not_none)] = None
    sample_name: str | None = None
    sex: Annotated[str | None, BeforeValidator(field_not_none)] = None
    subject_id: str | None = None
    tissue_type: str | None = None
    model_config = ConfigDict(validate_assignment=True)


class ScoutMipIndividual(ScoutIndividual):
    mt_bam: str | None = None
    chromograph_images: ChromographImages = ChromographImages()
    reviewer: Reviewer = Reviewer()
    rhocall_bed: str | None = None
    rhocall_wig: str | None = None
    tiddit_coverage_wig: str | None = None
    upd_regions_bed: str | None = None
    upd_sites_bed: str | None = None
    vcf2cytosure: str | None = None
    mitodel_file: str | None = None


class ScoutRarediseaseIndividual(ScoutIndividual):
    mt_bam: str | None = None
    chromograph_images: ChromographImages = ChromographImages()
    rhocall_bed: str | None = None
    rhocall_wig: str | None = None
    tiddit_coverage_wig: str | None = None
    upd_regions_bed: str | None = None
    upd_sites_bed: str | None = None
    vcf2cytosure: str | None = None
    mitodel_file: str | None = None
    reviewer: Reviewer = Reviewer()


class ScoutCancerIndividual(ScoutIndividual):
    tumor_type: str | None = None
    tmb: str | None = None
    msi: str | None = None
    tumor_purity: float = 0
    vcf2cytosure: str | None = None


class ScoutLoadConfig(BaseModel):
    owner: Annotated[str, BeforeValidator(field_not_none)] = None
    family: Annotated[str, BeforeValidator(field_not_none)] = None
    family_name: str | None = None
    synopsis: str | None = None
    phenotype_terms: list[str] | None = None
    phenotype_groups: list[str] | None = None
    gene_panels: list[str] | None = None
    default_gene_panels: list[str] = []
    cohorts: list[str] | None = None
    human_genome_build: str = None
    rank_model_version: str | None = None
    rank_score_threshold: int = None
    sv_rank_model_version: str | None = None
    analysis_date: datetime | None = None
    samples: list[ScoutIndividual] = []
    customer_images: CustomImages | None = None
    delivery_report: str | None = None
    coverage_qc_report: str | None = None
    cnv_report: str | None = None
    multiqc: str | None = None
    track: Literal[UploadTrack.RARE_DISEASE.value, UploadTrack.CANCER.value] = (
        UploadTrack.RARE_DISEASE.value
    )
    model_config = ConfigDict(validate_assignment=True)


class BalsamicLoadConfig(ScoutLoadConfig):
    madeline: str | None = None
    vcf_cancer: Annotated[str, BeforeValidator(field_not_none)] = None
    vcf_cancer_sv: str | None = None
    vcf_cancer_research: str | None = None
    vcf_cancer_sv_research: str | None = None
    samples: list[ScoutCancerIndividual] = []


class BalsamicUmiLoadConfig(BalsamicLoadConfig):
    pass


class MipLoadConfig(ScoutLoadConfig):
    chromograph_image_files: list[str] | None = None
    chromograph_prefixes: list[str] | None = None
    madeline: str | None = None
    peddy_check: str | None = None
    peddy_ped: str | None = None
    peddy_sex: str | None = None
    samples: list[ScoutMipIndividual] = []
    smn_tsv: str | None = None
    variant_catalog: str | None = None
    vcf_mei: str | None = None
    vcf_mei_research: str | None = None
    vcf_snv: Annotated[str, BeforeValidator(field_not_none)] = None
    vcf_snv_research: Annotated[str | None, BeforeValidator(field_not_none)] = None
    vcf_str: str | None = None
    vcf_sv: Annotated[str | None, BeforeValidator(field_not_none)] = None
    vcf_sv_research: Annotated[str | None, BeforeValidator(field_not_none)] = None


class RarediseaseLoadConfig(ScoutLoadConfig):
    madeline: str | None = None
    peddy_check: str | None = None
    peddy_ped: str | None = None
    peddy_sex: str | None = None
    samples: list[ScoutRarediseaseIndividual] = []
    custom_images: CustomImages | None = None
    smn_tsv: str | None = None
    str_catalog: str | None = None
    vcf_mei: str | None = None
    vcf_mei_research: str | None = None
    vcf_snv: Annotated[str, BeforeValidator(field_not_none)] = None
    vcf_snv_research: Annotated[str | None, BeforeValidator(field_not_none)] = None
    vcf_snv_mt: str | None = None
    vcf_snv_research_mt: str | None = None
    vcf_sv: Annotated[str | None, BeforeValidator(field_not_none)] = None
    vcf_sv_research: Annotated[str | None, BeforeValidator(field_not_none)] = None
    vcf_str: str | None = None


class RnafusionLoadConfig(ScoutLoadConfig):
    multiqc_rna: str | None = None
    gene_fusion: str | None = None
    gene_fusion_report_research: str | None = None
    RNAfusion_inspector: str | None = None
    RNAfusion_inspector_research: str | None = None
    RNAfusion_report: str | None = None
    RNAfusion_report_research: str | None = None
    samples: list[ScoutCancerIndividual] = []
    vcf_fusion: str | None = None
