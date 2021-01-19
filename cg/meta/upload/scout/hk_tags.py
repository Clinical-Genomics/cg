from typing import Dict, Set

from pydantic import BaseModel


class TagInfo(BaseModel):
    scout_field: str
    hk_tags: Set[str]


class HkTagMap(BaseModel):
    case_tags: Dict[str, TagInfo]
    sample_tags: Dict[str, TagInfo] = None


class CaseTags(BaseModel):
    snv_vcf: TagInfo
    snv_research_vcf: TagInfo = None
    sv_vcf: TagInfo
    sv_research_vcf: TagInfo = None
    multiqc_report: TagInfo = TagInfo(scout_field="multiqc", hk_tags={"multiqc-html"})
    delivery_report: TagInfo = TagInfo(scout_field="delivery_report", hk_tags={"delivery-report"})


class MipCaseTags(CaseTags):
    snv_vcf = TagInfo(scout_field="vcf_snv", hk_tags={"vcf-snv-clinical"})
    snv_research_vcf = TagInfo(scout_field="vcf_snv_research", hk_tags={"vcf-snv-research"})
    sv_vcf = (TagInfo(scout_field="vcf_sv", hk_tags={"vcf-sv-clinical"}),)
    sv_research_vcf = TagInfo(scout_field="vcf_sv_research", hk_tags={"vcf-sv-research"})
    vcf_str = TagInfo(scout_field="vcf_str", hk_tags={"vcf-str"})
    smn_tsv = TagInfo(scout_field="smn_tsv", hk_tags={"smn-calling"})
    peddy_ped = TagInfo(scout_field="peddy_ped", hk_tags={"ped", "peddy"})
    peddy_sex = TagInfo(scout_field="peddy_sex", hk_tags={"sex-check", "peddy"})
    peddy_check = TagInfo(scout_field="peddy_check", hk_tags={"ped-check", "peddy"})


class BalsamicCaseTags(CaseTags):
    snv_vcf = TagInfo(scout_field="vcf_cancer", hk_tags={"vcf-snv-clinical"})
    sv_vcf = TagInfo(scout_field="vcf_cancer_sv", hk_tags={"vcf-sv-clinical"})


class SampleTags(BaseModel):
    # If cram does not exist
    bam_file: TagInfo = TagInfo(scout_field="alignment_path", hk_tags={"bam"})
    alignment_file: TagInfo = TagInfo(scout_field="alignment_path", hk_tags={"cram"})


class BalsamicSampleTags(SampleTags):
    pass


class MipSampleTags(SampleTags):
    vcf2cytosure: TagInfo = TagInfo(scout_field="vcf2cytosure", hk_tags={"vcf2cytosure"})
    mt_bam: TagInfo = TagInfo(scout_field="mt_bam", hk_tags={"bam-mt"})
    chromograph_autozyg: TagInfo = TagInfo(
        scout_field="chromograph_images.autozyg", hk_tags={"chromograph", "autozyg"}
    )
    chromograph_coverage: TagInfo = TagInfo(
        scout_field="chromograph_images.coverage", hk_tags={"chromograph", "tcov"}
    )
    chromograph_regions: TagInfo = TagInfo(
        scout_field="chromograph_images.upd_regions", hk_tags={"chromograph", "regions"}
    )
    chromograph_sites: TagInfo = TagInfo(
        scout_field="chromograph_images.upd_sites", hk_tags={"chromograph", "sites"}
    )
