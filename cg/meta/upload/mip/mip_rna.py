"""MIP-RNA upload API"""

import logging

from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.meta.upload.mip.mip import MipUploadAPI


LOG = logging.getLogger(__name__)


class MipRNAUploadAPI(MipUploadAPI):
    """MIP-RNA upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: MipRNAAnalysisAPI = MipRNAAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)
