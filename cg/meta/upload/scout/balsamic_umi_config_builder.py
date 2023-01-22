import logging

from cg.constants.scout_upload import BALSAMIC_UMI_CASE_TAGS, BALSAMIC_UMI_SAMPLE_TAGS
from cg.meta.upload.scout.hk_tags import CaseTags, SampleTags
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.apps.lims import LimsAPI
from cg.models.scout.scout_load_config import BalsamicUmiLoadConfig, ScoutBalsamicIndividual
from cg.store import models

from housekeeper.store import models as hk_models

LOG = logging.getLogger(__name__)


class BalsamicUmiConfigBuilder(BalsamicConfigBuilder):
    def __init__(
        self, hk_version_obj: hk_models.Version, analysis_obj: models.Analysis, lims_api: LimsAPI
    ):
        super().__init__(
            hk_version_obj=hk_version_obj, analysis_obj=analysis_obj, lims_api=lims_api
        )
        self.case_tags: CaseTags = CaseTags(**BALSAMIC_UMI_CASE_TAGS)
        self.sample_tags: SampleTags = SampleTags(**BALSAMIC_UMI_SAMPLE_TAGS)
        self.load_config: BalsamicUmiLoadConfig = BalsamicUmiLoadConfig(track="cancer")

    def include_sample_files(self, config_sample: ScoutBalsamicIndividual) -> None:
        LOG.info("Including BALSAMIC specific sample level files")

    def get_balsamic_analysis_type(self, sample: models.Sample) -> str:
        """Returns a formatted balsamic analysis type"""

        return "panel-umi"
