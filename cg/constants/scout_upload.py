MIP_CASE_TAGS = dict(
    snv_vcf={"vcf-snv-clinical"},
    snv_research_vcf={"vcf-snv-research"},
    sv_vcf={"vcf-sv-clinical"},
    sv_research_vcf={"vcf-sv-research"},
    vcf_str={"vcf-str"},
    smn_tsv={"smn-calling"},
    peddy_ped={"ped", "peddy"},
    peddy_sex={"sex-check", "peddy"},
    peddy_check={"ped-check", "peddy"},
    multiqc_report={"multiqc-html"},
    delivery_report={"delivery-report"},
)

BALSAMIC_CASE_TAGS = dict(
    snv_vcf={"vcf-snv-clinical"},
    sv_vcf={"vcf-sv-clinical"},
    multiqc_report={"multiqc-html"},
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
)

BALSAMIC_SAMPLE_TAGS = dict(
    bam_file={"bam"},
    alignment_file={"cram"},
)
