"""MIP-DNA upload API"""

import logging

import click

from cg.cli.generate.report.base import delivery_report
from cg.cli.upload.scout import scout
from cg.cli.upload.observations import observations
from cg.cli.upload.genotype import genotypes
from cg.cli.upload.validate import validate
from cg.cli.upload.coverage import coverage
from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.cli.upload.gens import gens
from cg.constants import DataDelivery, REPORT_SUPPORTED_DATA_DELIVERY
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.meta.upload.upload_api import UploadAPI
from cg.store import models

LOG = logging.getLogger(__name__)


class MipDNAUploadAPI(UploadAPI):
    """MIP-DNA upload API"""

    def __init__(self, config: CGConfig, analysis_api: MipDNAAnalysisAPI):
        super().__init__(config=config, analysis_api=analysis_api)

    def upload(self, ctx: click.Context, case_obj: models.Family, restart: bool) -> None:
        """Uploads MIP-DNA analysis data and files"""

        analysis_obj: models.Analysis = case_obj.analyses[0]
        self.update_upload_started_at(analysis_obj)

        # Delivery report generation
        if case_obj.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(delivery_report, case_id=case_obj.internal_id)

        # Main upload
        ctx.invoke(coverage, family_id=case_obj.internal_id, re_upload=restart)
        ctx.invoke(validate, family_id=case_obj.internal_id)
        ctx.invoke(genotypes, family_id=case_obj.internal_id, re_upload=restart)
        ctx.invoke(observations, case_id=case_obj.internal_id)
        ctx.invoke(gens, case_id=case_obj.internal_id)

        # Clinical delivery upload
        ctx.invoke(clinical_delivery, case_id=case_obj.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case_obj.data_delivery:
            ctx.invoke(scout, case_id=case_obj.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case_obj.internal_id} and "
                f"the specified data delivery ({case_obj.data_delivery})"
            )

        self.update_uploaded_at(analysis_obj)
