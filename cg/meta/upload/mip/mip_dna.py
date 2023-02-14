"""MIP-DNA upload API"""

import logging

from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.meta.upload.mip.mip import MipUploadAPI


LOG = logging.getLogger(__name__)


class MipDNAUploadAPI(MipUploadAPI):
    """MIP-DNA upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: MipDNAAnalysisAPI = MipDNAAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
