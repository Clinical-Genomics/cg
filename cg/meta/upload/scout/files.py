"""Functions that handle files in the context of scout uploading"""
import logging
import re
from typing import Dict, List, Optional, Set, Tuple

from housekeeper.store import models as hk_models
from pydantic import BaseModel

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutBalsamicIndividual,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutMipIndividual,
)

LOG = logging.getLogger(__name__)

# Maps keys that are used in scout load config on tags that are used in scout


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


class ScoutFileHandler:
    def __init__(self, hk_version_obj: hk_models.Version):
        self.hk_version_obj: hk_models.Version = hk_version_obj
        self.case_tags = CaseTags()
        self.sample_tags = SampleTags()

    def include_sample_files(self, sample: ScoutIndividual):
        raise NotImplementedError

    def include_case_files(self, case: ScoutLoadConfig):
        raise NotImplementedError

    def include_sample_alignment_file(self, sample: ScoutIndividual) -> None:
        """Include the alignment file for a sample

        First add the bam.
        Cram is preferred so overwrite if found
        """
        sample_id: str = sample.sample_id
        bam_tag_obj: TagInfo = self.sample_tags.bam_file
        sample.alignment_path = self.fetch_sample_file(tag_map=bam_tag_obj, sample_id=sample_id)

        cram_tag_obj: TagInfo = self.sample_tags.alignment_file
        sample.alignment_path = self.fetch_sample_file(tag_map=cram_tag_obj, sample_id=sample_id)

    def fetch_sample_file(self, tag_map: TagInfo, sample_id: str) -> Optional[str]:
        """Fetch a file that is specific for a individual from housekeeper"""
        tags: set = tag_map.hk_tags.copy()
        tags.add(sample_id)
        return self.fetch_file_from_hk(hk_tags=tags)

    def fetch_file_from_hk(self, hk_tags: Set[str]) -> Optional[str]:
        """Fetch a file from housekeeper and return the path as a string.
        If file does not exist return None
        """
        hk_file: Optional[hk_models.File] = HousekeeperAPI.fetch_file_from_version(
            version_obj=self.hk_version_obj, tags=hk_tags
        )
        if hk_file is None:
            return hk_file
        return hk_file.full_path


class BalsamicFileHandler(ScoutFileHandler):
    def __init__(self, hk_version_obj: hk_models.Version):
        super().__init__(hk_version_obj=hk_version_obj)
        self.case_tags = BalsamicCaseTags()

    def include_sample_files(self, sample: ScoutBalsamicIndividual):
        pass

    def include_case_files(self, case: BalsamicLoadConfig):
        pass


class MipFileHandler(ScoutFileHandler):
    def __init__(self, hk_version_obj: hk_models.Version):
        super().__init__(hk_version_obj=hk_version_obj)
        self.case_tags = MipCaseTags()
        self.sample_tags = MipSampleTags()

    def include_case_files(self, case: MipLoadConfig):
        """Include case level files for mip case"""
        case.vcf_snv = self.fetch_file_from_hk(self.case_tags.snv_vcf.hk_tags)
        case.vcf_sv = self.fetch_file_from_hk(self.case_tags.sv_vcf.hk_tags)
        case.vcf_snv_research = self.fetch_file_from_hk(self.case_tags.snv_research_vcf.hk_tags)
        case.vcf_sv_research = self.fetch_file_from_hk(self.case_tags.sv_research_vcf.hk_tags)
        case.vcf_str = self.fetch_file_from_hk(self.case_tags.vcf_str.hk_tags)
        case.peddy_ped = self.fetch_file_from_hk(self.case_tags.peddy_ped.hk_tags)
        case.peddy_sex = self.fetch_file_from_hk(self.case_tags.peddy_sex.hk_tags)
        case.peddy_check = self.fetch_file_from_hk(self.case_tags.peddy_check.hk_tags)
        case.smn_tsv = self.fetch_file_from_hk(self.case_tags.smn_tsv.hk_tags)

    def include_sample_files(self, sample=ScoutMipIndividual) -> None:
        """Include sample level files that are optional for mip samples"""
        sample_id: str = sample.sample_id
        cytosure_tags: TagInfo = self.sample_tags.vcf2cytosure
        LOG.debug(
            "Including vcf2cytosure with tags %s for sample %s", cytosure_tags.hk_tags, sample_id
        )
        sample.vcf2cytosure = self.fetch_sample_file(tag_map=cytosure_tags, sample_id=sample_id)

        mt_bam_tag_obj: TagInfo = self.sample_tags.mt_bam
        LOG.debug(
            "Including mithocondrial bam with tags %s for sample %s",
            mt_bam_tag_obj.hk_tags,
            sample_id,
        )
        sample.mt_bam = self.fetch_sample_file(tag_map=mt_bam_tag_obj, sample_id=sample_id)

        autozyg_regions_tags: TagInfo = self.sample_tags.chromograph_autozyg
        LOG.debug(
            "Including autozygotic regions file with tags %s for sample %s",
            autozyg_regions_tags.hk_tags,
            sample_id,
        )
        sample.chromograph_images.autozyg = self.fetch_sample_file(
            tag_map=autozyg_regions_tags, sample_id=sample_id
        )

        chromograph_coverage_tags = self.sample_tags.chromograph_coverage
        LOG.debug(
            "Including chromograph coverage file with tags %s for sample %s",
            chromograph_coverage_tags.hk_tags,
            sample_id,
        )
        sample.chromograph_images.coverage = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(tag_map=chromograph_coverage_tags, sample_id=sample_id)
        )

        upd_region_tags = self.sample_tags.chromograph_regions
        LOG.debug(
            "Including upd regions files with tags %s for sample %s",
            upd_region_tags.hk_tags,
            sample_id,
        )
        sample.chromograph_images.upd_regions = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(tag_map=upd_region_tags, sample_id=sample_id)
        )

        upd_site_tags: TagInfo = self.sample_tags.chromograph_sites
        LOG.debug(
            "Including upd site files with tags %s for sample %s", upd_site_tags.hk_tags, sample_id
        )
        sample.chromograph_images.upd_sites = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(tag_map=upd_site_tags, sample_id=sample_id)
        )

    @staticmethod
    def extract_generic_filepath(file_path: Optional[str]) -> Optional[str]:
        """Remove a file's suffix and identifying integer or X/Y
        Example:
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png` becomes
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_`"""
        if file_path is None:
            return file_path
        return re.split("(\d+|X|Y)\.png", file_path)[0]
