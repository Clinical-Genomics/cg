import logging

from housekeeper.store.models import Version

from cg.apps.lims import LimsAPI
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.scout import BALSAMIC_UMI_CASE_TAGS, BALSAMIC_UMI_SAMPLE_TAGS, UploadTrack
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.models.scout.scout_load_config import BalsamicUmiLoadConfig, ScoutCancerIndividual
from cg.store.models import Analysis, Sample

LOG = logging.getLogger(__name__)


class BalsamicUmiConfigBuilder(BalsamicConfigBuilder):
    def __init__(self, hk_version_obj: Version, analysis_obj: Analysis, lims_api: LimsAPI):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_UMI_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_UMI_SAMPLE_TAGS)
        self.load_config: BalsamicUmiLoadConfig = BalsamicUmiLoadConfig(
            track=UploadTrack.CANCER.value,
            delivery_report=self.get_file_from_hk({HK_DELIVERY_REPORT_TAG}),
        )

    def include_sample_files(self, config_sample: ScoutCancerIndividual) -> None:
        LOG.info("Including BALSAMIC specific sample level files")

    def get_balsamic_analysis_type(self, sample: Sample) -> str:
        """Returns a formatted balsamic analysis type."""
        return "panel-umi"
