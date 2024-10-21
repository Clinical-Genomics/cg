import pytest

from cg.cli.post_process.utils import UnprocessedRunInfo
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService


@pytest.fixture
def pacbio_unprocessed_run_info(
    pacbio_sequencing_run_name: str, pac_bio_post_processing_service: PacBioPostProcessingService
) -> UnprocessedRunInfo:
    return UnprocessedRunInfo(
        name=pacbio_sequencing_run_name,
        post_processing_service=pac_bio_post_processing_service,
        instrument="pacbio",
    )


@pytest.fixture
def pacbio_barcoded_unprocessed_run_info(
    pacbio_barcoded_sequencing_run_name: str,
    pac_bio_post_processing_service: PacBioPostProcessingService,
) -> UnprocessedRunInfo:
    return UnprocessedRunInfo(
        name=pacbio_barcoded_sequencing_run_name,
        post_processing_service=pac_bio_post_processing_service,
        instrument="pacbio",
    )


@pytest.fixture
def pacbio_unprocessed_runs(
    pacbio_unprocessed_run_info: UnprocessedRunInfo,
    pacbio_barcoded_unprocessed_run_info: UnprocessedRunInfo,
) -> list[UnprocessedRunInfo]:
    return [pacbio_unprocessed_run_info, pacbio_barcoded_unprocessed_run_info]
