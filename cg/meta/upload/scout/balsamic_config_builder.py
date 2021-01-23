import logging

from housekeeper.store import models as hk_models

from cg.apps.lims import LimsAPI
from cg.constants.scout_upload import BALSAMIC_CASE_TAGS, BALSAMIC_SAMPLE_TAGS
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.scout_config_builder import LOG, ScoutConfigBuilder
from cg.meta.upload.scout.scout_load_config import BalsamicLoadConfig, ScoutBalsamicIndividual
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.store import models

LOG = logging.getLogger(__name__)


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
