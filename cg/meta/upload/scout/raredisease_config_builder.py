import logging
import re
from pathlib import Path

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    RAREDISEASE_CASE_TAGS,
    RAREDISEASE_SAMPLE_TAGS,
    UploadTrack,
)
from cg.constants.subject import RelationshipStatus
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.models.scout.scout_load_config import (
    CaseImages,
    CustomImages,
    Eklipse,
    RarediseaseLoadConfig,
    ScoutIndividual,
    ScoutLoadConfig,
    ScoutRarediseaseIndividual,
)
from cg.store.models import Analysis, Case, CaseSample, Sample

LOG = logging.getLogger(__name__)


class RarediseaseConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self,
        hk_version_obj: Version,
        analysis_obj: Analysis,
        raredisease_analysis_api: RarediseaseAnalysisAPI,
        lims_api: LimsAPI,
        madeline_api: MadelineAPI,
    ):
        super().__init__(
            hk_version_obj=hk_version_obj,
            analysis_obj=analysis_obj,
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**RAREDISEASE_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**RAREDISEASE_SAMPLE_TAGS)
        self.load_config: RarediseaseLoadConfig = RarediseaseLoadConfig(
            track=UploadTrack.RARE_DISEASE.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.raredisease_analysis_api: RarediseaseAnalysisAPI = raredisease_analysis_api
        self.lims_api: LimsAPI = lims_api
        self.madeline_api: MadelineAPI = madeline_api

    def build_load_config(self) -> RarediseaseLoadConfig:
        """Create a RAREDISEASE specific load config for uploading analysis to Scout."""
        LOG.info("Build load config for RAREDISEASE case")
        self.load_config = self.add_common_info_to_load_config()
        self.load_config.gene_panels = (
            self.raredisease_analysis_api.get_aggregated_panels(
                customer_id=self.analysis_obj.case.customer.internal_id,
                default_panels=set(self.analysis_obj.case.panels),
            )
        )
        self.load_config = self.include_case_files(load_config=self.load_config)
        self.load_config.samples = self._get_sample_information()
        self.load_config = self.include_pedigree_picture(load_config=self.load_config)
        self.load_config.custom_images = self.load_custom_image_sample()
        return self.load_config


    def _get_sample_information(self):
        LOG.info("Building samples")
        self.load_config = ScoutLoadConfig()
        db_sample: CaseSample
        for db_sample in self.analysis_obj.case.links:
            self.load_config.samples.append(self.build_config_sample(case_sample=db_sample))
        return self.load_config



    def build_config_sample(self, case_sample: CaseSample) -> ScoutRarediseaseIndividual:
        """Build a sample with specific information."""
        config_sample = ScoutRarediseaseIndividual()
        self.add_common_sample_info(config_sample=config_sample, case_sample=case_sample)
        self.add_common_sample_files(config_sample=config_sample, case_sample=case_sample)
        self.include_sample_files(config_sample=config_sample)
        return config_sample

    def load_custom_image_sample(self) -> CustomImages:
        """Build custom images config."""
        LOG.info("Adding custom images")
        eklipse_images: list = []
        for db_sample in self.analysis_obj.case.links:
            sample_id: str = db_sample.sample.internal_id
            eklipse_image = Eklipse(
                title=sample_id,
                path=self.get_file_from_hk(hk_tags=self.sample_tags.eklipse_path),
                description="eKLIPse MT images",
                width="800",
                height="800",
            )
            eklipse_images.append(eklipse_image)

        case_images = CaseImages(eKLIPse=eklipse_images)
        config_custom_images = CustomImages(case_images=case_images)
        return config_custom_images

    def include_case_files(self, load_config: ScoutLoadConfig) -> None:
        """Include case level files for mip case."""
        LOG.info("Including RAREDISEASE specific case level files")
        for scout_key in RAREDISEASE_CASE_TAGS.keys():
            self._include_case_file(load_config, scout_key)

    def _include_case_file(self, load_config: ScoutLoadConfig, scout_key: str) -> ScoutLoadConfig:
        """Include the file path associated to a scout configuration parameter if the corresponding housekeeper tags
        are found. Otherwise return None."""
        file_path = self.get_file_from_hk(getattr(self.case_tags, scout_key))
        setattr(load_config, scout_key, file_path)
        return load_config

    def include_sample_files(self, config_sample: ScoutRarediseaseIndividual) -> ScoutRarediseaseIndividual:
        """Include sample level files that are optional for mip samples."""
        LOG.info("Including RAREDISEASE specific sample level files")
        sample_id: str = config_sample.sample_id
        config_sample.vcf2cytosure = self.get_sample_file(
            hk_tags=self.sample_tags.vcf2cytosure, sample_id=sample_id
        )
        config_sample.mt_bam = self.get_sample_file(
            hk_tags=self.sample_tags.mt_bam, sample_id=sample_id
        )
        config_sample.chromograph_images.autozygous = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_autozyg, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.coverage = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_coverage, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_regions = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_regions, sample_id=sample_id
            )
        )
        config_sample.chromograph_images.upd_sites = self.remove_chromosome_substring(
            file_path=self.get_sample_file(
                hk_tags=self.sample_tags.chromograph_sites, sample_id=sample_id
            )
        )
        config_sample.reviewer.alignment = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment, sample_id=sample_id
        )
        config_sample.reviewer.alignment_index = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_alignment_index, sample_id=sample_id
        )
        config_sample.reviewer.vcf = self.get_sample_file(
            hk_tags=self.sample_tags.reviewer_vcf, sample_id=sample_id
        )
        config_sample.reviewer.catalog = self.get_file_from_hk(hk_tags=self.case_tags.str_catalog)
        config_sample.mitodel_file = self.get_sample_file(
            hk_tags=self.sample_tags.mitodel_file, sample_id=sample_id
        )
        return config_sample

    @staticmethod
    def remove_chromosome_substring(file_path: str | None) -> str | None:
        """Remove a file's suffix and identifying integer or X/Y
        Example:
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_X.png` becomes
        `/some/path/gatkcomb_rhocall_vt_af_chromograph_sites_`"""
        if file_path is None:
            return file_path
        return re.sub(r"(_(?:\d+|X|Y))\.png$", "", file_path)

    def include_sample_alignment_file(self, config_sample: ScoutIndividual) -> None:
        """Include the CRAM alignment file for a sample."""
        sample_id: str = config_sample.sample_id
        config_sample.alignment_path = self.get_sample_file(
            hk_tags=self.sample_tags.alignment_file, sample_id=sample_id
        )
