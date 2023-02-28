"""Balsamic upload API"""

import datetime as dt
import logging

import click

from cg.cli.generate.report.base import delivery_report
from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.cli.upload.genotype import genotypes
from cg.cli.upload.observations import observations
from cg.cli.upload.scout import scout
from cg.constants import REPORT_SUPPORTED_DATA_DELIVERY, DataDelivery
from cg.constants.sequencing import SequencingMethod
from cg.meta.upload.gt import UploadGenotypesAPI
from cg.meta.upload.upload_api import UploadAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


class BalsamicUploadAPI(UploadAPI):
    """Balsamic upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case: models.Family, restart: bool) -> None:
        """Uploads BALSAMIC analysis data and files"""

        analysis_obj: models.Analysis = case.analyses[0]

        self.update_upload_started_at(analysis_obj)

        # Delivery report generation
        if case.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(delivery_report, case_id=case.internal_id)

        # Clinical delivery
        ctx.invoke(clinical_delivery, case_id=case.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case.data_delivery:
            ctx.invoke(scout, case_id=case.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case.internal_id} and "
                f"the specified data delivery ({case.data_delivery})"
            )

        # Genotype specific upload
        if UploadGenotypesAPI.is_suitable_for_genotype_upload(case):
            ctx.invoke(genotypes, family_id=case.internal_id, re_upload=restart)
        else:
            LOG.info(f"Balsamic case {case.internal_id} is not compatible for Genotype upload")

        # Observations upload
        if self.analysis_api.get_case_application_type(case.internal_id) == SequencingMethod.WGS:
            ctx.invoke(observations, case_id=case.internal_id)
        else:
            LOG.info(f"Balsamic case {case.internal_id} is not compatible for Observations upload")

        LOG.info(
            f"Upload of case {case.internal_id} was successful. Setting uploaded at to {dt.datetime.now()}"
        )
        self.update_uploaded_at(analysis_obj)
