from enum import StrEnum, auto

from cg.constants import FileExtensions
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG, AlignmentFileTag, AnalysisTag

HGNC_ID = "hgnc_id"


class GenomeBuild(StrEnum):
    hg19: str = "37"
    hg38: str = "38"


class ScoutExportFileName(StrEnum):
    MANAGED_VARIANTS: str = f"managed_variants{FileExtensions.VCF}"
    PANELS: str = f"gene_panels{FileExtensions.BED}"


class UploadTrack(StrEnum):
    RARE_DISEASE: str = "rare"
    CANCER: str = "cancer"


class ScoutCustomCaseReportTags(StrEnum):
    DELIVERY: str = "delivery_report"
    CNV: str = "cnv_report"
    COV_QC: str = "coverage_qc_report"
    MULTIQC: str = "multiqc"
    MULTIQC_RNA: str = "multiqc_rna"
    GENE_FUSION: str = "gene_fusion"
    GENE_FUSION_RESEARCH: str = "gene_fusion_research"


class ScoutUploadKey(StrEnum):
    FRASER_TSV = auto()
    OUTRIDER_TSV = auto()
    SMN_TSV = auto()
    SNV_RESEARCH_VCF = auto()
    SNV_VCF = auto()
    SV_VCF = auto()
    VCF_FUSION = auto()
    VCF_STR = auto()


RAREDISEASE_CASE_TAGS = dict(
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

MIP_CASE_TAGS: dict[str, set[str]] = RAREDISEASE_CASE_TAGS

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
    cnv_report={"cnv-report"},
    multiqc_report={"multiqc-html"},
    delivery_report={"delivery-report"},
)

RNAFUSION_CASE_TAGS: dict[str, set[str]] = dict(
    multiqc_rna={"multiqc-html", "rna"},
    gene_fusion={"arriba-visualisation", "clinical"},
    gene_fusion_report_research={"arriba-visualisation", "research"},
    RNAfusion_report={"fusionreport", "clinical"},
    RNAfusion_report_research={"fusionreport", "research"},
    RNAfusion_inspector={"fusioninspector-html", "clinical"},
    RNAfusion_inspector_research={"fusioninspector-html", "research"},
    delivery_report={"delivery-report"},
    vcf_fusion={"vcf-fusion"},
)

TOMTE_CASE_TAGS: dict[str, set[str]] = dict(
    multiqc_rna={AnalysisTag.MULTIQC_HTML, AnalysisTag.RNA},
    delivery_report={HK_DELIVERY_REPORT_TAG},
    snv_research_vcf={AnalysisTag.RESEARCH, AnalysisTag.VCF, AnalysisTag.SNV},
    snv_vcf={AnalysisTag.CLINICAL, AnalysisTag.VCF, AnalysisTag.SNV},
    fraser_tsv={AnalysisTag.CLINICAL, AnalysisTag.FRASER},
    outrider_tsv={AnalysisTag.CLINICAL, AnalysisTag.OUTRIDER},
)


RAREDISEASE_SAMPLE_TAGS = dict(
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

MIP_SAMPLE_TAGS: dict[str, set[str]] = RAREDISEASE_SAMPLE_TAGS

BALSAMIC_SAMPLE_TAGS = dict(
    bam_file={"bam"},
    alignment_file={"cram"},
    vcf2cytosure={"vcf2cytosure"},
)

BALSAMIC_UMI_SAMPLE_TAGS = dict(
    bam_file={"umi-bam"},
    alignment_file={"umi-cram"},
)


RNAFUSION_SAMPLE_TAGS = dict(
    alignment_file={AlignmentFileTag.CRAM},
)

TOMTE_SAMPLE_TAGS = dict(
    alignment_file={AlignmentFileTag.CRAM},
    splice_junctions_bed={"junction", "bed"},
    rna_coverage_bigwig={"coverage", "bigwig"},
)
