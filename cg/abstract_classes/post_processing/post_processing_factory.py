"""Post-processing service factory."""

from pathlib import Path

from cg.abstract_classes.post_processing.post_processing_service import PostProcessingService
from cg.abstract_classes.post_processing.post_processing_service_provider import (
    PostProcessingServiceProvider,
)
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.services.illumina.service_provider import IlluminaPostProcessServiceProvider
from cg.store.store import Store


class PostProcessingServiceFactory:
    def __int__(self, status_db: Store, hk_api: HousekeeperAPI, dry_run: bool, run_dir: Path):
        self.status_db: Store = status_db
        self.hk_api: HousekeeperAPI = hk_api
        self.run_dir: Path = run_dir
        self.dry_run: bool = dry_run

    def _get_service_provider(
        self,
    ) -> PostProcessingServiceProvider:
        if "illumina" in self.run_dir.as_posix():
            return IlluminaPostProcessServiceProvider(
                status_db=self.status_db,
                hk_api=self.hk_api,
                run_dir=self.run_dir,
                dry_run=self.dry_run,
            )

    def create_post_processing_service(self) -> PostProcessingService:
        provider = self._get_service_provider()
        return provider.create_post_processing_service()
