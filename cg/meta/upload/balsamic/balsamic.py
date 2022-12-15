"""Balsamic upload API"""

import logging

import click
from cg.cli.upload.observations import observations

from cg.cli.generate.report.base import delivery_report
from cg.cli.upload.scout import scout
from cg.cli.upload.genotype import genotypes
from cg.cli.upload.clinical_delivery import clinical_delivery
from cg.constants import DataDelivery, REPORT_SUPPORTED_DATA_DELIVERY
from cg.constants.sequencing import SequencingMethod
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.meta.upload.upload_api import UploadAPI
from cg.store import models
from cg.meta.upload.gt import UploadGenotypesAPI

LOG = logging.getLogger(__name__)


class BalsamicUploadAPI(UploadAPI):
    """Balsamic upload API"""

    def __init__(self, config: CGConfig):
        self.analysis_api: BalsamicAnalysisAPI = BalsamicAnalysisAPI(config)
        super().__init__(config=config, analysis_api=self.analysis_api)

    def upload(self, ctx: click.Context, case_obj: models.Family, restart: bool) -> None:
        """Uploads BALSAMIC analysis data and files"""

        analysis_obj: models.Analysis = case_obj.analyses[0]

        self.update_upload_started_at(analysis_obj)

        # Delivery report generation
        if case_obj.data_delivery in REPORT_SUPPORTED_DATA_DELIVERY:
            ctx.invoke(delivery_report, case_id=case_obj.internal_id)

        # Clinical delivery
        ctx.invoke(clinical_delivery, case_id=case_obj.internal_id)

        # Scout specific upload
        if DataDelivery.SCOUT in case_obj.data_delivery:
            ctx.invoke(scout, case_id=case_obj.internal_id, re_upload=restart)
        else:
            LOG.warning(
                f"There is nothing to upload to Scout for case {case_obj.internal_id} and "
                f"the specified data delivery ({case_obj.data_delivery})"
            )

        # Genotype specific upload
        if UploadGenotypesAPI.is_suitable_for_genotype_upload(case_obj):
            ctx.invoke(genotypes, family_id=case_obj.internal_id, re_upload=restart)
        else:
            LOG.info(f"Balsamic case {case_obj.internal_id} is not compatible for Genotype upload")

        # Observations upload
        if (
            self.analysis_api.get_case_application_type(case_obj.internal_id)
            == SequencingMethod.WGS
        ):
            ctx.invoke(observations, case_id=case_obj.internal_id)
        else:
            LOG.info(
                f"Balsamic case {case_obj.internal_id} is not compatible for Observations upload"
            )

        self.update_uploaded_at(analysis_obj)
