"""Maps tag info from housekeeper tags to scout load config"""

from typing import Set

from pydantic import BaseModel, Field


class CaseTags(BaseModel):
    snv_vcf: Set[str] = Field(..., description="vcf_snv for rare disease and vcf_cancer for cancer")
    snv_research_vcf: Set[str] = Field(None, description="vcf_snv_research for rare disease")
    sv_vcf: Set[str] = Field(
        ..., description="vcf_cancer_sv for rare disease and vcf_sv_cancer for cancer"
    )
    sv_research_vcf: Set[str] = Field(None, description="vcf_sv_research for rare disease")
    vcf_str: Set[str] = Field(
        None, description="Short Tandem Repeat variants, only for rare disease"
    )
    smn_tsv: Set[str] = Field(None, description="SMN gene variants, only for rare disease")
    peddy_ped: Set[str] = Field(None, description="Ped info from peddy, only for rare disease")
    peddy_sex: Set[str] = Field(None, description="Peddy sex check, only for rare disease")
    peddy_check: Set[str] = Field(None, description="Peddy pedigree check, only for rare disease")
    multiqc_report: Set[str]
    delivery_report: Set[str]


class SampleTags(BaseModel):
    # If cram does not exist
    bam_file: Set[str]
    alignment_file: Set[str]
    vcf2cytosure: Set[str] = None
    mt_bam: Set[str] = None
    chromograph_autozyg: Set[str] = None
    chromograph_coverage: Set[str] = None
    chromograph_regions: Set[str] = None
    chromograph_sites: Set[str] = None
