import logging
from pathlib import Path

from cg.services.run_devices.abstract_classes import PostProcessingService
from cg.services.run_devices.constants import POST_PROCESSING_COMPLETED
from cg.services.run_devices.error_handler import handle_post_processing_errors
from cg.services.run_devices.exc import (
    PostProcessingError,
    PostProcessingRunDataGeneratorError,
    PostProcessingStoreDataError,
    PostProcessingStoreFileError,
)
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.run_devices.pacbio.run_data_generator.pacbio_run_data_generator import (
    PacBioRunDataGenerator,
)
from cg.services.run_devices.pacbio.run_data_generator.run_data import PacBioRunData
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator

LOG = logging.getLogger(__name__)


class PacBioPostProcessingService(PostProcessingService):
    """Service for handling post-processing of PacBio sequencing runs."""

    def __init__(
        self,
        run_validator: PacBioRunValidator,
        run_data_generator: PacBioRunDataGenerator,
        hk_service: PacBioHousekeeperService,
        store_service: PacBioStoreService,
        sequencing_dir: str,
    ):
        self.run_validator: PacBioRunValidator = run_validator
        self.run_data_generator: PacBioRunDataGenerator = run_data_generator
        self.hk_service: PacBioHousekeeperService = hk_service
        self.store_service: PacBioStoreService = store_service
        self.sequencing_dir: str = sequencing_dir

    @handle_post_processing_errors(
        to_except=(
            PostProcessingStoreDataError,
            PostProcessingRunDataGeneratorError,
            PostProcessingStoreFileError,
        ),
        to_raise=PostProcessingError,
    )
    def post_process(self, run_name: str, dry_run: bool = False) -> None:
        LOG.info(f"Starting Pacbio post-processing for run: {run_name}")
        run_data: PacBioRunData = self.run_data_generator.get_run_data(
            run_name=run_name, sequencing_dir=self.sequencing_dir
        )
        self.run_validator.ensure_post_processing_can_start(run_data)
        self.store_service.store_post_processing_data(run_data=run_data, dry_run=dry_run)
        self.hk_service.store_files_in_housekeeper(run_data=run_data, dry_run=dry_run)
        self._touch_post_processing_complete(run_data=run_data, dry_run=dry_run)

    def is_run_processed(self, run_name: str) -> bool:
        """Check if a run has been post-processed."""
        processing_complete_file = Path(self.sequencing_dir, run_name, POST_PROCESSING_COMPLETED)
        return processing_complete_file.exists()
