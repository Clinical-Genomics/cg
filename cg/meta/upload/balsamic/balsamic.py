"""Balsamic upload API."""

import datetime as dt
import logging

import click

from cg.apps.gens import GensAPI
from cg.cli.generate.report.base import generate_delivery_report
from cg.cli.upload.clinical_delivery import upload_clinical_delivery
from cg.cli.upload.genotype import upload_genotypes
from cg.cli.upload.gens import upload_to_gens
from cg.cli.upload.observations import upload_observations_to_loqusdb
from cg.cli.upload.scout import upload_to_scout
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.constants.sequencing import SequencingMethod
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class BalsamicUploadAPI(UploadAPI):
    """Balsamic upload API."""

    def __init__(self, config: CGConfig):
        self.analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Uploads BALSAMIC analysis data and files."""
        analysis: Analysis = case.analyses[0]
        self.update_upload_started_at(analysis=analysis)

        # Delivery report generation
        if case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(generate_delivery_report, case_id=case.internal_id)

        # Clinical delivery
        ctx.invoke(upload_clinical_delivery, case_id=case.internal_id)

        if GensAPI.is_suitable_for_upload(case):
            ctx.invoke(upload_to_gens, case_id=case.internal_id)
        else:
            LOG.info(f"Balsamic case {case.internal_id} is not compatible for Gens upload")

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(upload_to_scout, case_id=case.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case.internal_id} and "
                f"the specified data delivery ({case.data_delivery})"
            )

        # Genotype specific upload
        if UploadGenotypesAPI.is_suitable_for_genotype_upload(case_obj=case):
            ctx.invoke(upload_genotypes, family_id=case.internal_id, re_upload=restart)
        else:
            LOG.info(f"Balsamic case {case.internal_id} is not compatible for Genotype upload")

        # Observations upload
        if (
            self.analysis_api.get_case_application_type(case_id=case.internal_id)
            == SequencingMethod.WGS
        ):
            ctx.invoke(upload_observations_to_loqusdb, case_id=case.internal_id)
        else:
            LOG.info(f"Balsamic case {case.internal_id} is not compatible for Observations upload")
        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )

        self.update_uploaded_at(analysis=analysis)
