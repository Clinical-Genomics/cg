"""Functions that handle files in the context of scout uploading"""
import logging
import re
from pathlib import Path
from typing import Optional, Set

import requests
from housekeeper.store import models as hk_models

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scout_load_config import (
    BalsamicLoadConfig,
    MipLoadConfig,
    ScoutBalsamicIndividual,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutMipIndividual,
)
from cg.constants.scout_upload import (
    BALSAMIC_CASE_TAGS,
    BALSAMIC_SAMPLE_TAGS,
    MIP_CASE_TAGS,
    MIP_SAMPLE_TAGS,
)
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip import MipAnalysisAPI
from cg.store import models

LOG = logging.getLogger(__name__)

# Maps keys that are used in scout load config on tags that are used in scout


class ScoutConfigBuilder:
    """Base class for handling files that should be included in Scout upload"""

    def __init__(
        self, hk_version_obj: hk_models.Version, analysis_obj: models.Analysis, lims_api: LimsAPI
    ):
        self.hk_version_obj: hk_models.Version = hk_version_obj
        self.analysis_obj: models.Analysis = analysis_obj
        self.lims_api: LimsAPI = lims_api
        self.case_tags: CaseTags = CaseTags()
        self.sample_tags: SampleTags = SampleTags()
        self.load_config: ScoutLoadConfig = ScoutLoadConfig()

    def add_mandatory_info_to_load_config(self) -> None:
        """Add the mandatory common information to a scout load config object"""
        self.load_config.analysis_date = self.analysis_obj.completed_at
        self.load_config.default_gene_panels = self.analysis_obj.family.panels
        self.load_config.family = self.analysis_obj.family.internal_id
        self.load_config.family_name = self.analysis_obj.family.name
        self.load_config.owner = self.analysis_obj.family.customer.internal_id

        self.include_case_files()

    def add_mandatory_sample_info(
        self,
        sample: ScoutIndividual,
        sample_obj: models.FamilySample,
        sample_name: Optional[str] = None,
    ) -> None:
        """Add the information to a sample that is common for different analysis types"""
        sample_id: str = sample_obj.sample.internal_id
        LOG.info("Building sample %s", sample_id)
        lims_sample = dict()
        try:
            lims_sample = self.lims_api.sample(sample_id) or {}
        except requests.exceptions.HTTPError as ex:
            LOG.info("Could not fetch sample %s from LIMS: %s", sample_id, ex)

        sample.sample_id = sample_id
        sample.sex = sample_obj.sample.sex
        sample.phenotype = sample_obj.status
        sample.analysis_type = sample_obj.sample.application_version.application.analysis_type
        sample.sample_name = sample_name or sample_obj.sample.name
        sample.tissue_type = lims_sample.get("source", "unknown")

        self.include_sample_alignment_file(sample=sample)
        self.include_sample_files(sample=sample)

    def build_config_sample(self, sample_obj: models.FamilySample) -> ScoutIndividual:
        """Build a sample for the scout load config"""
        raise NotImplementedError

    def build_load_config(self) -> ScoutLoadConfig:
        """Build a load config for uploading a case to scout"""
        raise NotImplementedError

    def include_sample_files(self, sample: ScoutIndividual) -> None:
        """Include all files that are used on sample level in Scout"""
        raise NotImplementedError

    def include_case_files(self, load_config: ScoutLoadConfig) -> None:
        """Include all files that are used on case level in scout"""
        raise NotImplementedError

    def include_multiqc_report(self) -> None:
        LOG.info("Include MultiQC report to case")
        self.load_config.multiqc = self.fetch_file_from_hk(self.case_tags.multiqc_report)

    def include_delivery_report(self) -> None:
        LOG.info("Include delivery report to case")
        self.load_config.delivery_report = self.fetch_file_from_hk(self.case_tags.delivery_report)

    def include_sample_alignment_file(self, sample: ScoutIndividual) -> None:
        """Include the alignment file for a sample

        First add the bam.
        Cram is preferred so overwrite if found
        """
        sample_id: str = sample.sample_id
        sample.alignment_path = self.fetch_sample_file(
            hk_tags=self.sample_tags.bam_file, sample_id=sample_id
        )

        sample.alignment_path = self.fetch_sample_file(
            hk_tags=self.sample_tags.alignment_file, sample_id=sample_id
        )

    def fetch_sample_file(self, hk_tags: Set[str], sample_id: str) -> Optional[str]:
        """Fetch a file that is specific for a individual from housekeeper"""
        tags: set = hk_tags.copy()
        tags.add(sample_id)
        return self.fetch_file_from_hk(hk_tags=tags)

    def fetch_file_from_hk(self, hk_tags: Set[str]) -> Optional[str]:
        """Fetch a file from housekeeper and return the path as a string.
        If file does not exist return None
        """
        if not hk_tags:
            return None
        hk_file: Optional[hk_models.File] = HousekeeperAPI.fetch_file_from_version(
            version_obj=self.hk_version_obj, tags=hk_tags
        )
        if hk_file is None:
            return hk_file
        return hk_file.full_path


class BalsamicConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self, hk_version_obj: hk_models.Version, analysis_obj: models.Analysis, lims_api: LimsAPI
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_SAMPLE_TAGS)
        self.load_config: BalsamicLoadConfig = BalsamicLoadConfig(track="cancer")

    def include_case_files(self):
        LOG.info("Including BALSAMIC specific case level files")
        self.load_config.vcf_cancer = self.fetch_file_from_hk(self.case_tags.snv_vcf)
        self.load_config.vcf_cancer_sv = self.fetch_file_from_hk(self.case_tags.sv_vcf)
        self.include_multiqc_report()

    def include_sample_files(self, sample: ScoutBalsamicIndividual):
        LOG.info("Including BALSAMIC specific sample level files")

    def build_config_sample(self, sample_obj: models.FamilySample) -> ScoutBalsamicIndividual:
        """Build a sample with balsamic specific information"""
        sample = ScoutBalsamicIndividual()
        # This will be tumor or normal
        sample_name: str = BalsamicAnalysisAPI.get_sample_type(sample_obj)
        self.add_mandatory_sample_info(
            sample=sample, sample_obj=sample_obj, sample_name=sample_name
        )
        return sample

    def build_load_config(self) -> None:
        LOG.info("Build load config for balsamic case")
        self.add_mandatory_info_to_load_config()
        self.load_config.human_genome_build = "37"
        self.load_config.rank_score_threshold = 0

        LOG.info("Building samples")
        sample: models.FamilySample
        for sample in self.analysis_obj.family.links:
            self.load_config.samples.append(self.build_config_sample(sample_obj=sample))


class MipConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        hk_version_obj: hk_models.Version,
        analysis_obj: models.Analysis,
        mip_analysis_api: MipAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**MIP_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**MIP_SAMPLE_TAGS)
        self.load_config: MipLoadConfig = MipLoadConfig(track="rare")
        self.mip_analysis_api: MipAnalysisAPI = mip_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self, rank_score_threshold: int = 5) -> None:
        """Create a MIP specific load config for uploading analysis to Scout"""
        LOG.info("Generate load config for mip case")

        self.add_mandatory_info_to_load_config()
        analysis_data: dict = self.mip_analysis_api.get_latest_metadata(
            self.analysis_obj.family.internal_id
        )
        self.load_config.human_genome_build = (
            "38" if "38" in analysis_data.get("genome_build", "") else "37"
        )
        self.load_config.rank_score_threshold = rank_score_threshold
        self.load_config.rank_model_version = analysis_data.get("rank_model_version")
        self.load_config.sv_rank_model_version = analysis_data.get("sv_rank_model_version")

        self.load_config.gene_panels = (
            self.mip_analysis_api.convert_panels(
                self.analysis_obj.family.customer.internal_id, self.analysis_obj.family.panels
            )
            or None
        )

        LOG.info("Building samples")
        sample: models.FamilySample
        for sample in self.analysis_obj.family.links:
            self.load_config.samples.append(self.build_config_sample(sample_obj=sample))

        if self.is_multi_sample_case(self.load_config):
            if self.is_family_case(self.load_config):
                svg_path: Path = self._run_madeline(self.analysis_obj.family)
                self.load_config.madeline = str(svg_path)
            else:
                LOG.info("family of unconnected samples - skip pedigree graph")
        else:
            LOG.info("family of 1 sample - skip pedigree graph")

    def build_config_sample(self, sample_obj: models.FamilySample) -> ScoutMipIndividual:
        """Build a sample with mip specific information"""

        sample = ScoutMipIndividual()
        self.add_mandatory_sample_info(sample=sample, sample_obj=sample_obj)
        sample.father = sample_obj.father.internal_id if sample_obj.father else "0"
        sample.mother = sample_obj.mother.internal_id if sample_obj.mother else "0"

        return sample

    def include_case_files(self, load_config: MipLoadConfig):
        """Include case level files for mip case"""
        LOG.info("Including MIP specific case level files")
        self.load_config.vcf_snv = self.fetch_file_from_hk(self.case_tags.snv_vcf)
        self.load_config.vcf_sv = self.fetch_file_from_hk(self.case_tags.sv_vcf)
        self.load_config.vcf_snv_research = self.fetch_file_from_hk(self.case_tags.snv_research_vcf)
        self.load_config.vcf_sv_research = self.fetch_file_from_hk(self.case_tags.sv_research_vcf)
        self.load_config.vcf_str = self.fetch_file_from_hk(self.case_tags.vcf_str)
        self.load_config.peddy_ped = self.fetch_file_from_hk(self.case_tags.peddy_ped)
        self.load_config.peddy_sex = self.fetch_file_from_hk(self.case_tags.peddy_sex)
        self.load_config.peddy_check = self.fetch_file_from_hk(self.case_tags.peddy_check)
        self.load_config.smn_tsv = self.fetch_file_from_hk(self.case_tags.smn_tsv)
        self.include_multiqc_report()
        self.include_delivery_report()

    def include_sample_files(self, sample: ScoutMipIndividual) -> None:
        """Include sample level files that are optional for mip samples"""
        LOG.info("Including MIP specific sample level files")
        sample_id: str = sample.sample_id
        sample.vcf2cytosure = self.fetch_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )
        sample.mt_bam = self.fetch_sample_file(hk_tags=self.sample_tags.mt_bam, sample_id=sample_id)
        sample.chromograph_images.autozyg = self.fetch_sample_file(
            hk_tags=self.sample_tags.chromograph_autozyg, sample_id=sample_id
        )
        sample.chromograph_images.coverage = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(
                hk_tags=self.sample_tags.chromograph_coverage, sample_id=sample_id
            )
        )
        sample.chromograph_images.upd_regions = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(
                hk_tags=self.sample_tags.chromograph_regions, sample_id=sample_id
            )
        )
        sample.chromograph_images.upd_sites = self.extract_generic_filepath(
            file_path=self.fetch_sample_file(
                hk_tags=self.sample_tags.chromograph_sites, sample_id=sample_id
            )
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

    @staticmethod
    def is_multi_sample_case(load_config: ScoutLoadConfig) -> bool:
        return len(load_config.samples) > 1

    def run_madeline(self, family_obj: models.Family) -> Path:
        """Generate a madeline file for an analysis. Use customer sample names"""
        samples = [
            {
                "sample": link_obj.sample.name,
                "sex": link_obj.sample.sex,
                "father": link_obj.father.name if link_obj.father else None,
                "mother": link_obj.mother.name if link_obj.mother else None,
                "status": link_obj.status,
            }
            for link_obj in family_obj.links
        ]
        svg_path: Path = self.madeline_api.run(family_id=family_obj.name, samples=samples)
        return svg_path
