"""Functions that handle files in the context of scout uploading"""
import logging
import re
from typing import Optional, Set

from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutBalsamicIndividual,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.meta.upload.scout.hk_tags import (
    BalsamicCaseTags,
    BalsamicSampleTags,
    CaseTags,
    MipCaseTags,
    MipSampleTags,
    SampleTags,
    TagInfo,
)

LOG = logging.getLogger(__name__)

# Maps keys that are used in scout load config on tags that are used in scout


class ScoutFileHandler:
    """Base class for handling files that should be included in Scout upload"""

    def __init__(self, hk_version_obj: hk_models.Version):
        self.hk_version_obj: hk_models.Version = hk_version_obj
        self.case_tags = CaseTags()
        self.sample_tags = SampleTags()

    def include_sample_files(self, sample: ScoutIndividual) -> None:
        """Include all files that are used on sample level in Scout"""
        raise NotImplementedError

    def include_case_files(self, case: ScoutLoadConfig) -> None:
        """Include all files that are used on case level in scout"""
        raise NotImplementedError

    def include_multiqc_report(self, case: ScoutLoadConfig) -> None:
        LOG.info("Include MultiQC report to case")
        case.multiqc = self.fetch_file_from_hk(self.case_tags.multiqc_report.hk_tags)

    def include_delivery_report(self, case: ScoutLoadConfig) -> None:
        LOG.info("Include delivery report to case")
        case.delivery_report = self.fetch_file_from_hk(self.case_tags.delivery_report.hk_tags)

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
        self.case_tags: BalsamicCaseTags = BalsamicCaseTags()
        self.sample_tags: BalsamicSampleTags = BalsamicSampleTags()

    def include_case_files(self, case: BalsamicLoadConfig):
        LOG.info("Including BALSAMIC specific case level files")
        case.vcf_cancer = self.fetch_file_from_hk(self.case_tags.snv_vcf.hk_tags)
        case.vcf_cancer_sv = self.fetch_file_from_hk(self.case_tags.sv_vcf.hk_tags)
        self.include_multiqc_report(case)

    def include_sample_files(self, sample: ScoutBalsamicIndividual):
        LOG.info("Including BALSAMIC specific sample level files")


class MipFileHandler(ScoutFileHandler):
    def __init__(self, hk_version_obj: hk_models.Version):
        super().__init__(hk_version_obj=hk_version_obj)
        self.case_tags = MipCaseTags()
        self.sample_tags = MipSampleTags()

    def include_case_files(self, case: MipLoadConfig):
        """Include case level files for mip case"""
        LOG.info("Including MIP specific case level files")
        case.vcf_snv = self.fetch_file_from_hk(self.case_tags.snv_vcf.hk_tags)
        case.vcf_sv = self.fetch_file_from_hk(self.case_tags.sv_vcf.hk_tags)
        case.vcf_snv_research = self.fetch_file_from_hk(self.case_tags.snv_research_vcf.hk_tags)
        case.vcf_sv_research = self.fetch_file_from_hk(self.case_tags.sv_research_vcf.hk_tags)
        case.vcf_str = self.fetch_file_from_hk(self.case_tags.vcf_str.hk_tags)
        case.peddy_ped = self.fetch_file_from_hk(self.case_tags.peddy_ped.hk_tags)
        case.peddy_sex = self.fetch_file_from_hk(self.case_tags.peddy_sex.hk_tags)
        case.peddy_check = self.fetch_file_from_hk(self.case_tags.peddy_check.hk_tags)
        case.smn_tsv = self.fetch_file_from_hk(self.case_tags.smn_tsv.hk_tags)
        self.include_multiqc_report(case)
        self.include_delivery_report(case)

    def include_sample_files(self, sample: ScoutMipIndividual) -> None:
        """Include sample level files that are optional for mip samples"""
        LOG.info("Including MIP specific sample level files")
        sample_id: str = sample.sample_id
        cytosure_tags: TagInfo = self.sample_tags.vcf2cytosure
        LOG.debug(
            "Including vcf2cytosure with tags %s for sample %s", cytosure_tags.hk_tags, sample_id
        )
        sample.vcf2cytosure = self.fetch_sample_file(tag_map=cytosure_tags, sample_id=sample_id)

        mt_bam_tag_obj: TagInfo = self.sample_tags.mt_bam
        LOG.debug(
            "Including mitochondrial bam with tags %s for sample %s",
            mt_bam_tag_obj.hk_tags,
            sample_id,
        )
        sample.mt_bam = self.fetch_sample_file(tag_map=mt_bam_tag_obj, sample_id=sample_id)

        autozyg_regions_tags: TagInfo = self.sample_tags.chromograph_autozyg
        LOG.debug(
            "Including autozygous regions file with tags %s for sample %s",
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
