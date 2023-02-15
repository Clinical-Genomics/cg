"""MIP-RNA upload API"""

import logging

import click

from cg.cli.upload.scout import upload_rna_to_scout
from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.constants import DataDelivery
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


class MipRNAUploadAPI(UploadAPI):
    """MIP-RNA upload API"""

    def __init__(self, config: CGConfig, analysis_api: MipRNAAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def upload(self, ctx: click.Context, case_obj: models.Family, restart: bool) -> None:
        """Uploads MIP-RNA analysis data and files"""

        analysis_obj: models.Analysis = case_obj.analyses[0]
        self.update_upload_started_at(analysis_obj)

        # Clinical delivery upload
        ctx.invoke(clinical_delivery, case_id=case_obj.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case_obj.data_delivery:
            ctx.invoke(upload_rna_to_scout, case_id=case_obj.internal_id)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case_obj.internal_id} and "
                f"the specified data delivery ({case_obj.data_delivery})"
            )

        self.update_uploaded_at(analysis_obj)
