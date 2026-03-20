from pathlib import Path

from click import Context

from cg.meta.upload.upload_api import UploadAPI
from cg.models.cg_config import CGConfig
from cg.services.deliver_files import deliver_raw_data
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.store.models import Case
from cg.store.store import Store


class RawDataUploadAPI(UploadAPI):
    def __init__(self, config: CGConfig) -> None:
        self.status_db: Store = config.status_db
        self.delivery_path: Path = Path(config.delivery_path)
        self.delivery_service_factory: DeliveryServiceFactory = config.delivery_service_factory

    def upload(self, ctx: Context, case: Case, restart: bool) -> None:
        """Deliver raw data for all analyses in a case"""
        deliver_raw_data.deliver_analyses(
            analyses=case.analyses,
            status_db=self.status_db,
            delivery_path=self.delivery_path,
            service_builder=self.delivery_service_factory,
            dry_run=False,
        )
