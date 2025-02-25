import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import (
    BALSAMIC_UMI_CASE_TAGS,
    BALSAMIC_UMI_SAMPLE_TAGS,
    GenomeBuild,
    UploadTrack,
)
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.models.scout.scout_load_config import BalsamicUmiLoadConfig, ScoutCancerIndividual
from cg.store.models import Analysis, CaseSample, Sample

LOG = logging.getLogger(__name__)


class BalsamicUmiConfigBuilder(BalsamicConfigBuilder):
    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj,
            analysis_obj=analysis_obj,
            lims_api=lims_api,
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_UMI_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_UMI_SAMPLE_TAGS)

    def build_load_config(self) -> BalsamicUmiLoadConfig:
        LOG.info("Build load config for balsamic case")
        load_config: BalsamicUmiLoadConfig = BalsamicUmiLoadConfig(
            track=UploadTrack.CANCER.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )
        self.add_common_info_to_load_config(load_config)
        load_config.human_genome_build = GenomeBuild.hg19
        load_config.rank_score_threshold = -100
        self.include_case_files(load_config)

        LOG.info("Building samples")
        db_sample: CaseSample

        for db_sample in self.analysis_obj.case.links:
            load_config.samples.append(self.build_config_sample(case_sample=db_sample))

        return load_config

    def include_sample_files(self, config_sample: ScoutCancerIndividual) -> None:
        LOG.info("Including BALSAMIC specific sample level files")

    def get_balsamic_analysis_type(self, sample: Sample) -> str:
        """Returns a formatted balsamic analysis type."""
        return "panel-umi"
