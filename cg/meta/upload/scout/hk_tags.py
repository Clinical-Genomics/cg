"""Maps tag info from housekeeper tags to scout load config"""

from typing import Optional, Set

from pydantic.v1 import BaseModel, Field


class CaseTags(BaseModel):
    snv_vcf: Optional[Set[str]] = Field(
        None, description="vcf_snv for rare disease and vcf_cancer for cancer"
    )
    snv_research_vcf: Optional[Set[str]] = Field(
        None, description="vcf_snv_research for rare disease"
    )
    sv_vcf: Optional[Set[str]] = Field(
        None, description="vcf_cancer_sv for rare disease and vcf_sv_cancer for cancer"
    )
    sv_research_vcf: Optional[Set[str]] = Field(
        None, description="vcf_sv_research for rare disease"
    )
    vcf_str: Set[str] = Field(
        None, description="Short Tandem Repeat variants, only for rare disease"
    )
    cnv_report: Optional[Set[str]] = Field(
        None, description="AscatNgs visualization report for cancer"
    )
    smn_tsv: Optional[Set[str]] = Field(
        None, description="SMN gene variants, only for rare disease"
    )
    peddy_ped: Set[str] = Field(None, description="Ped info from peddy, only for rare disease")
    peddy_sex: Optional[Set[str]] = Field(
        None, description="Peddy sex check, only for rare disease"
    )
    peddy_check: Set[str] = Field(None, description="Peddy pedigree check, only for rare disease")
    multiqc_report: Optional[Set[str]] = Field(None, description="MultiQC report")
    delivery_report: Optional[Set[str]] = Field(None, description="Delivery report")
    str_catalog: Optional[Set[str]] = Field(
        None, description="Variant catalog used with expansionhunter"
    )
    gene_fusion: Set[str] = Field(
        None, description="Arriba report for RNA fusions containing only clinical fusions"
    )
    gene_fusion_report_research: Optional[Set[str]] = Field(
        None, description="Arriba report for RNA fusions containing all fusions"
    )
    RNAfusion_report: Optional[Set[str]] = Field(
        None, description="Main RNA fusion report containing only clinical fusions"
    )
    RNAfusion_report_research: Optional[Set[str]] = Field(
        None, description="Main RNA fusion report containing all fusions"
    )
    RNAfusion_inspector: Optional[Set[str]] = Field(
        None, description="RNAfusion inspector report containing only clinical fusions"
    )
    RNAfusion_inspector_research: Optional[Set[str]] = Field(
        None, description="RNAfusion inspector report containing all fusions"
    )
    multiqc_rna: Optional[Set[str]] = Field(None, description="MultiQC report for RNA samples")
    vcf_mei: Optional[Set[str]] = Field(
        None, description="VCF with mobile element insertions, clinical"
    )
    vcf_mei_research: Optional[Set[str]] = Field(
        None, description="VCF with mobile element insertions, research"
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
