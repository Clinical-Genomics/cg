from typing import Dict, Set

from cg.utils.enums import StrEnum


class GenomeBuild(StrEnum):
    hg19: str = "37"
    hg38: str = "38"


class ScoutCustomCaseReportTags(StrEnum):
    DELIVERY: str = "delivery_report"
    CNV: str = "cnv_report"
    COV_QC: str = "coverage_qc_report"
    MULTIQC: str = "multiqc"
    MULTIQC_RNA: str = "multiqc_rna"
    GENE_FUSION: str = "gene_fusion"
    GENE_FUSION_RESEARCH: str = "gene_fusion_research"


MIP_CASE_TAGS = dict(
    delivery_report={"delivery-report"},
    multiqc_report={"multiqc-html"},
    peddy_check={"ped-check", "peddy"},
    peddy_ped={"ped", "peddy"},
    peddy_sex={"sex-check", "peddy"},
    smn_tsv={"smn-calling"},
    snv_research_vcf={"vcf-snv-research"},
    snv_vcf={"vcf-snv-clinical"},
    str_catalog={"expansionhunter", "variant-catalog"},
    sv_research_vcf={"vcf-sv-research"},
    sv_vcf={"vcf-sv-clinical"},
    vcf_mei={"mobile-elements", "clinical", "vcf"},
    vcf_mei_research={"mobile-elements", "research", "vcf"},
    vcf_str={"vcf-str"},
)

BALSAMIC_CASE_TAGS = dict(
    sv_vcf={"vcf-sv-clinical"},
    snv_vcf={"vcf-snv-clinical"},
    cnv_report={"cnv-report"},
    multiqc_report={"multiqc-html"},
    delivery_report={"delivery-report"},
)

BALSAMIC_UMI_CASE_TAGS = dict(
    sv_vcf={"vcf-sv-clinical"},
    snv_vcf={"vcf-umi-snv-clinical"},
    multiqc_report={"multiqc-html"},
    delivery_report={"delivery-report"},
)

RNAFUSION_CASE_TAGS: Dict[str, Set[str]] = dict(
    multiqc_rna={"multiqc-html", "rna"},
    gene_fusion={"arriba-visualisation", "clinical"},
    gene_fusion_report_research={"arriba-visualisation", "research"},
    RNAfusion_report={"fusionreport", "clinical"},
    RNAfusion_report_research={"fusionreport", "research"},
    RNAfusion_inspector={"fusioninspector-html", "clinical"},
    RNAfusion_inspector_research={"fusioninspector-html", "research"},
    delivery_report={"delivery-report"},
)

MIP_SAMPLE_TAGS = dict(
    bam_file={"bam"},
    alignment_file={"cram"},
    vcf2cytosure={"vcf2cytosure"},
    mt_bam={"bam-mt"},
    chromograph_autozyg={"chromograph", "autozyg"},
    chromograph_coverage={"chromograph", "tcov"},
    chromograph_regions={"chromograph", "regions"},
    chromograph_sites={"chromograph", "sites"},
    reviewer_alignment={"expansionhunter", "bam"},
    reviewer_alignment_index={"expansionhunter", "bam-index"},
    reviewer_vcf={"expansionhunter", "vcf-str"},
    mitodel_file={"mitodel"},
)

BALSAMIC_SAMPLE_TAGS = dict(
    bam_file={"bam"},
    alignment_file={"cram"},
    vcf2cytosure={"vcf2cytosure"},
)

BALSAMIC_UMI_SAMPLE_TAGS = dict(
    bam_file={"umi-bam"},
    alignment_file={"umi-cram"},
)


RNAFUSION_SAMPLE_TAGS = {}
