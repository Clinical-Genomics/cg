"""MIP-DNA upload API."""
import datetime as dt
import logging

import click

from cg.cli.generate.report.base import generate_delivery_report
from cg.cli.upload.clinical_delivery import upload_clinical_delivery
from cg.cli.upload.coverage import upload_coverage
from cg.cli.upload.genotype import upload_genotypes
from cg.cli.upload.gens import upload_to_gens
from cg.cli.upload.observations import upload_observations_to_loqusdb
from cg.cli.upload.scout import upload_to_scout
from cg.cli.upload.validate import validate
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Family

LOG = logging.getLogger(__name__)


class MipDNAUploadAPI(UploadAPI):
    """MIP-DNA upload API."""

    def __init__(self, config: CGConfig):
        self.analysis_api: MipDNAAnalysisAPI = MipDNAAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Family, restart: bool) -> None:
        """Uploads MIP-DNA analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        # Main upload
        ctx.invoke(upload_coverage, family_id=case.internal_id, re_upload=restart)
        ctx.invoke(validate, family_id=case.internal_id)
        ctx.invoke(upload_genotypes, family_id=case.internal_id, re_upload=restart)
        ctx.invoke(upload_observations_to_loqusdb, case_id=case.internal_id)
        ctx.invoke(upload_to_gens, case_id=case.internal_id)

        # Delivery report generation
        if case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(generate_delivery_report, case_id=case.internal_id)

        # Clinical delivery upload
        ctx.invoke(upload_clinical_delivery, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(upload_to_scout, case_id=case.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case.internal_id} and "
                f"the specified data delivery ({case.data_delivery})"
            )

        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )
        self.update_uploaded_at(analysis=analysis)
