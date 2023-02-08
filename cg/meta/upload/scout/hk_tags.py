"""Maps tag info from housekeeper tags to scout load config"""

from typing import Optional, Set

from pydantic import BaseModel, Field


class CaseTags(BaseModel):
    snv_vcf: Set[str] = Field(
        None, description="vcf_snv for rare disease and vcf_cancer for cancer"
    )
    # snv_vcf: Set[str] = Field(..., description="vcf_snv for rare disease and vcf_cancer for cancer")
    snv_research_vcf: Set[str] = Field(None, description="vcf_snv_research for rare disease")
    # sv_vcf: Set[str] = Field(
    #     ..., description="vcf_cancer_sv for rare disease and vcf_sv_cancer for cancer"
    # )
    sv_vcf: Set[str] = Field(
        None, description="vcf_cancer_sv for rare disease and vcf_sv_cancer for cancer"
    )
    sv_research_vcf: Set[str] = Field(None, description="vcf_sv_research for rare disease")
    vcf_str: Set[str] = Field(
        None, description="Short Tandem Repeat variants, only for rare disease"
    )
    cnv_report: Set[str] = Field(None, description="AscatNgs visualization report for cancer")
    smn_tsv: Set[str] = Field(None, description="SMN gene variants, only for rare disease")
    peddy_ped: Set[str] = Field(None, description="Ped info from peddy, only for rare disease")
    peddy_sex: Set[str] = Field(None, description="Peddy sex check, only for rare disease")
    peddy_check: Set[str] = Field(None, description="Peddy pedigree check, only for rare disease")
    multiqc_report: Set[str] = Field(None, description="MultiQC report")
    delivery_report: Set[str] = Field(None, description="Delivery report for cancer")
    str_catalog: Set[str] = Field(None, description="Variant catalog used with expansionhunter")
    genefusion_report: Set[str] = Field(
        None, description="Arriba report for RNA fusions containing only clinical fusions"
    )
    genefusion_report_research: Set[str] = Field(
        None, description="Arriba report for RNA fusions containing all fusions"
    )
    rnafusion_report: Set[str] = Field(
        None, description="Main RNA fusion report containing only clinical fusions"
    )
    rnafusion_report_research: Set[str] = Field(
        None, description="Main RNA fusion report containing all fusions"
    )
    rnafusion_inspector: Set[str] = Field(
        None, description="RNAfusion inspector report containing only clinical fusions"
    )
    rnafusion_inspector_research: Set[str] = Field(
        None, description="RNAfusion inspector report containing all fusions"
    )


class SampleTags(BaseModel):
    # If cram does not exist
    bam_file: Optional[Set[str]] = None
    alignment_file: Optional[Set[str]] = None
    vcf2cytosure: Optional[Set[str]] = None
    mt_bam: Optional[Set[str]] = None
    chromograph_autozyg: Optional[Set[str]] = None
    chromograph_coverage: Optional[Set[str]] = None
    chromograph_regions: Optional[Set[str]] = None
    chromograph_sites: Optional[Set[str]] = None
    reviewer_alignment: Optional[Set[str]] = None
    reviewer_alignment_index: Optional[Set[str]] = None
    reviewer_vcf: Optional[Set[str]] = None
    mitodel_file: Optional[Set[str]] = None
