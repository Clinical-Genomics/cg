"""Upload API"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import rich_click as click

from cg.exc import AnalysisAlreadyUploadedError, AnalysisUploadError
from cg.meta.meta import MetaAPI
from cg.meta.upload.error_handling import handle_delivery_type_errors
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Analysis, Case

LOG = logging.getLogger(__name__)


class UploadAPI(MetaAPI):
    """Upload API"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api: AnalysisAPI = analysis_api
        self.scout_upload_api: UploadScoutAPI = UploadScoutAPI(
            hk_api=config.housekeeper_api,
            scout_api=analysis_api.scout_api,
            madeline_api=config.madeline_api,
            analysis_api=self.analysis_api,
            lims_api=config.lims_api,
            status_db=config.status_db,
        )

    def upload(self, ctx: click.Context, case: Case, restart: bool) -> None:
        """Uploads workflow specific analysis data and files."""

        raise NotImplementedError

    def update_upload_started_at(self, analysis: Analysis) -> None:
        """Updates the upload_started_at field with the current local date and time"""

        analysis.upload_started_at = datetime.now()
        self.status_db.session.commit()

    def update_uploaded_at(self, analysis: Analysis) -> None:
        """Updates the uploaded_at field with the current local date and time"""

        analysis.uploaded_at: datetime = datetime.now()

        self.status_db.session.commit()
        self.trailblazer_api.set_analysis_uploaded(
            case_id=analysis.case.internal_id, uploaded_at=analysis.uploaded_at
        )

    @staticmethod
    def verify_analysis_upload(case_obj: Case, restart: bool) -> None:
        """Verifies the state of an analysis upload in StatusDB"""

        if not case_obj.data_delivery:
            LOG.error(f"The data delivery field has not been specified for: {case_obj.internal_id}")
            raise AnalysisUploadError

        if not case_obj.analyses:
            LOG.error(f"There is no analysis for case: {case_obj.internal_id}")
            raise AnalysisUploadError

        if not restart:
            analysis: Analysis = case_obj.analyses[0]

            if analysis.uploaded_at:
                LOG.error(f"The analysis has been already uploaded: {analysis.uploaded_at.date()}")
                raise AnalysisAlreadyUploadedError
            elif analysis.upload_started_at:
                if datetime.now() - analysis.upload_started_at > timedelta(hours=24):
                    LOG.error(
                        f"This upload has already started at {analysis.upload_started_at}, but something went wrong. "
                        f"Restart it with the --restart flag."
                    )
                    raise AnalysisUploadError

                LOG.warning(f"The upload has already started: {analysis.upload_started_at.time()}")
                raise AnalysisAlreadyUploadedError

    @handle_delivery_type_errors
    def upload_files_to_customer_inbox(self, case: Case) -> None:
        """Uploads the analysis files to the customer inbox."""
        factory_service: DeliveryServiceFactory = self.config.delivery_service_factory
        delivery_service: DeliverFilesService = factory_service.build_delivery_service(
            case=case, delivery_type=case.data_delivery
        )
        delivery_service.deliver_files_for_case(
            case=case, delivery_base_path=Path(self.config.delivery_path)
        )
