import logging

from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.apps.lims import LimsAPI
from cg.models.scout.scout_load_config import BalsamicUmiLoadConfig
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
        self.load_config: BalsamicUmiLoadConfig = BalsamicUmiLoadConfig(track="cancer")
