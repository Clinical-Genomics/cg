"""MIP-DNA upload API"""

import datetime as dt
import logging

import click

from cg.apps.tb import TrailblazerAPI
from cg.cli.generate.report.base import delivery_report
from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.cli.upload.coverage import coverage
from cg.cli.upload.genotype import genotypes
from cg.cli.upload.gens import gens
from cg.cli.upload.observations import observations
from cg.cli.upload.scout import scout
from cg.cli.upload.validate import validate
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


class MipDNAUploadAPI(UploadAPI):
    """MIP-DNA upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: MipDNAAnalysisAPI = MipDNAAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: models.Family, restart: bool) -> None:
        """Uploads MIP-DNA analysis data and files"""

        analysis_obj: models.Analysis = case.analyses[0]
        self.update_upload_started_at(analysis_obj)

        # Main upload
        ctx.invoke(coverage, family_id=case.internal_id, re_upload=restart)
        ctx.invoke(validate, family_id=case.internal_id)
        ctx.invoke(genotypes, family_id=case.internal_id, re_upload=restart)
        ctx.invoke(observations, case_id=case.internal_id)
        ctx.invoke(gens, case_id=case.internal_id)

        # Delivery report generation
        if case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(delivery_report, case_id=case.internal_id)

        # Clinical delivery upload
        ctx.invoke(clinical_delivery, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(scout, case_id=case.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case.internal_id} and "
                f"the specified data delivery ({case.data_delivery})"
            )

        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )
        self.update_uploaded_at(analysis_obj)
