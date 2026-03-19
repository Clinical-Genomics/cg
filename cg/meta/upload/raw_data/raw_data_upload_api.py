import logging
from datetime import datetime
from pathlib import Path

from click import Context

from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.services.deliver_files.deliver_files_service.deliver_files_service import (
    DeliverFilesService,
)
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Case
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class RawDataUploadAPI(UploadAPI):
    def __init__(self, config: CGConfig) -> None:
        self.status_db: Store = config.status_db
        self.delivery_path: Path = Path(config.delivery_path)
        self.delivery_service_factory: DeliveryServiceFactory = config.delivery_service_factory

    def upload(self, ctx: Context, case: Case, restart: bool) -> None:
        """Deliver raw data for all analyses in a case"""
        for analysis in case.analyses:
            try:
                delivery_service: DeliverFilesService = (
                    self.delivery_service_factory.build_delivery_service(
                        case=case, delivery_type=case.data_delivery
                    )
                )
                delivery_service.deliver_files_for_case(
                    case=case,
                    delivery_base_path=self.delivery_path,
                )
                self.status_db.update_analysis_upload_started_at(
                    analysis_id=analysis.id, upload_started_at=datetime.now()
                )
            except Exception as error:
                self.status_db.update_analysis_upload_started_at(
                    analysis_id=analysis.id, upload_started_at=None
                )
                LOG.error(f"Could not deliver files for analysis {analysis.id}: {error}")
                continue
