import logging

from cg.apps.lims import LimsAPI
from cg.constants.scout_upload import RNAFUSION_CASE_TAGS, RNAFUSION_SAMPLE_TAGS
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import ScoutConfigBuilder
from cg.models.scout.scout_load_config import RnafusionLoadConfig, ScoutIndividual
from cg.store import models
from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class RnafusionConfigBuilder(ScoutConfigBuilder):
    def __init__(
        self, hk_version_obj: hk_models.Version, analysis_obj: models.Analysis, lims_api: LimsAPI
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**RNAFUSION_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(*RNAFUSION_SAMPLE_TAGS)  # TODO
        self.load_config: RnafusionLoadConfig = RnafusionLoadConfig(
            track="cancer"
        )  # TODO: decide what to do with track

    def include_case_files(self):
        LOG.info("Including RNAFUSION specific case level files")
        self.include_multiqc_report()
        self.include_delivery_report()

    def build_config_sample(self, db_sample: models.FamilySample) -> ScoutIndividual:
        """Build a sample with rnafusion specific information"""
        config_sample = ScoutIndividual()

        # TODO: complete

        return config_sample

    def build_load_config(self) -> None:
        LOG.info("Build load config for rnafusion case")
        self.add_common_info_to_load_config()
        self.load_config.human_genome_build = "37"  # TODO: adapt
        self.load_config.rank_score_threshold = -100
        self.include_case_files()

        LOG.info("Building samples")
        db_sample: models.FamilySample

        for db_sample in self.analysis_obj.family.links:
            self.load_config.samples.append(self.build_config_sample(db_sample=db_sample))
