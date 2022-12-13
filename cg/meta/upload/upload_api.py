"""Upload API"""

import logging
from datetime import datetime, timedelta

import click
from cg.exc import AnalysisUploadError, AnalysisAlreadyUploadedError
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.cg_config import CGConfig
from cg.meta.meta import MetaAPI
from cg.store import models


LOG = logging.getLogger(__name__)


class UploadAPI(MetaAPI):
    """Upload API"""

    def __init__(self, config: CGConfig, analysis_api: AnalysisAPI):
        super().__init__(config=config)
        self.analysis_api = analysis_api
        self.scout_upload_api: UploadScoutAPI = UploadScoutAPI(
            hk_api=config.housekeeper_api,
            scout_api=config.scout_api,
            madeline_api=config.madeline_api,
            analysis_api=self.analysis_api,
            lims_api=config.lims_api,
            status_db=config.status_db,
        )

    def upload(self, ctx: click.Context, case_obj: models.Family, restart: bool) -> None:
        """Uploads pipeline specific analysis data and files"""

        raise NotImplementedError

    def update_upload_started_at(self, analysis: models.Analysis) -> None:
        """Updates the upload_started_at field with the current local date and time"""

        analysis.upload_started_at = datetime.now()
        self.status_db.commit()

    def update_uploaded_at(self, analysis: models.Analysis) -> None:
        """Updates the uploaded_at field with the current local date and time"""

        analysis.uploaded_at: datetime = datetime.now()

        self.status_db.commit()
        self.trailblazer_api.set_analysis_uploaded(
            case_id=analysis.family.internal_id, uploaded_at=analysis.uploaded_at
        )

    @staticmethod
    def verify_analysis_upload(case_obj: models.Family, restart: bool) -> None:
        """Verifies the state of an analysis upload in StatusDB"""

        if not case_obj.data_delivery:
            LOG.error(f"The data delivery field has not been specified for: {case_obj.internal_id}")
            raise AnalysisUploadError

        if not case_obj.analyses:
            LOG.error(f"There is no analysis for case: {case_obj.internal_id}")
            raise AnalysisUploadError

        analysis_obj: models.Analysis = case_obj.analyses[0]
        if analysis_obj.uploaded_at is not None:
            LOG.error(f"The analysis has been already uploaded: {analysis_obj.uploaded_at.date()}")
            raise AnalysisAlreadyUploadedError

        if not restart and analysis_obj.upload_started_at is not None:
            if datetime.now() - analysis_obj.upload_started_at > timedelta(hours=24):
                LOG.error(
                    f"This upload has already started at {analysis_obj.upload_started_at}, but something went wrong. "
                    f"Restart it with the --restart flag."
                )
                raise AnalysisUploadError

            LOG.warning(f"The upload has already started: {analysis_obj.upload_started_at.time()}")
            raise AnalysisAlreadyUploadedError
