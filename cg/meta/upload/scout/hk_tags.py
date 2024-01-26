"""Maps tag info from housekeeper tags to scout load config"""

from pydantic import BaseModel, Field


class CaseTags(BaseModel):
    snv_vcf: set[str] | None = Field(
        None, description="vcf_snv for rare disease and vcf_cancer for cancer"
    )
    snv_research_vcf: set[str] | None = Field(None, description="vcf_snv_research for rare disease")
    sv_vcf: set[str] | None = Field(
        None, description="vcf_cancer_sv for rare disease and vcf_sv_cancer for cancer"
    )
    sv_research_vcf: set[str] | None = Field(None, description="vcf_sv_research for rare disease")
    vcf_str: set[str] = Field(
        None, description="Short Tandem Repeat variants, only for rare disease"
    )
    cnv_report: set[str] | None = Field(None, description="CNV visualization report for cancer")
    smn_tsv: set[str] | None = Field(None, description="SMN gene variants, only for rare disease")
    peddy_ped: set[str] = Field(None, description="Ped info from peddy, only for rare disease")
    peddy_sex: set[str] | None = Field(None, description="Peddy sex check, only for rare disease")
    peddy_check: set[str] = Field(None, description="Peddy pedigree check, only for rare disease")
    multiqc_report: set[str] | None = Field(None, description="MultiQC report")
    delivery_report: set[str] | None = Field(None, description="Delivery report")
    str_catalog: set[str] | None = Field(
        None, description="Variant catalog used with expansionhunter"
    )
    gene_fusion: set[str] = Field(
        None, description="Arriba report for RNA fusions containing only clinical fusions"
    )
    gene_fusion_report_research: set[str] | None = Field(
        None, description="Arriba report for RNA fusions containing all fusions"
    )
    RNAfusion_report: set[str] | None = Field(
        None, description="Main RNA fusion report containing only clinical fusions"
    )
    RNAfusion_report_research: set[str] | None = Field(
        None, description="Main RNA fusion report containing all fusions"
    )
    RNAfusion_inspector: set[str] | None = Field(
        None, description="RNAfusion inspector report containing only clinical fusions"
    )
    RNAfusion_inspector_research: set[str] | None = Field(
        None, description="RNAfusion inspector report containing all fusions"
    )
    vcf_fusion: set[str] | None = Field(None, description="VCF with fusions, clinical")
    multiqc_rna: set[str] | None = Field(None, description="MultiQC report for RNA samples")
    vcf_mei: set[str] | None = Field(
        None, description="VCF with mobile element insertions, clinical"
    )
    vcf_mei_research: set[str] | None = Field(
        None, description="VCF with mobile element insertions, research"
    )


class SampleTags(BaseModel):
    # If cram does not exist
    bam_file: set[str] | None = None
    alignment_file: set[str] | None = None
    vcf2cytosure: set[str] | None = None
    mt_bam: set[str] | None = None
    chromograph_autozyg: set[str] | None = None
    chromograph_coverage: set[str] | None = None
    chromograph_regions: set[str] | None = None
    chromograph_sites: set[str] | None = None
    reviewer_alignment: set[str] | None = None
    reviewer_alignment_index: set[str] | None = None
    reviewer_vcf: set[str] | None = None
    mitodel_file: set[str] | None = None
