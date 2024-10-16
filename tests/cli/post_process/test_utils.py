import pytest

from cg.cli.post_process.utils import (
    UnprocessedRunInfo,
    get_post_processing_service_from_run_name,
    get_unprocessed_runs_info,
)
from cg.models.cg_config import CGConfig
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService


def are_lists_equal(list1: list[any], list2: list[any]) -> bool:
    """Returns whether two lists holed the same items, regardless of order."""
    if len(list1) != len(list2):
        return False
    return all(any(obj1 == obj2 for obj2 in list2) for obj1 in list1)


def test_get_post_processing_service_from_run_name(
    pac_bio_context: CGConfig, pacbio_barcoded_sequencing_run_name: str
):
    """Test that a the correct post processing service is returned given a run name."""
    # GIVEN a context with a post-processing service for the run name
    assert pac_bio_context.post_processing_services.pacbio

    # WHEN getting the post-processing service from the run name
    service: PacBioPostProcessingService = get_post_processing_service_from_run_name(
        context=pac_bio_context, run_name=pacbio_barcoded_sequencing_run_name
    )
    # THEN a the correct post-processing service should be returned
    assert isinstance(service, PacBioPostProcessingService)


@pytest.mark.parametrize(
    "wrong_run_name",
    [
        "m_84202_2024_05_22_133539/1_A01",
        "r84202_20240522133539/1_A01",
        "r84202_20240522_133539/3_A01",
    ],
    ids=["doesn't start with r", "incorrect splits", "incorrect plate"],
)
def test_get_post_processing_service_from_wrong_run_name(
    pac_bio_context: CGConfig, wrong_run_name: str
):
    """Test that a the correct post processing service is returned given a run name."""
    # GIVEN a wrong run name

    # GIVEN a context with a post-processing service for the run name
    assert pac_bio_context.post_processing_services.pacbio

    # WHEN getting the post-processing service from the run name
    with pytest.raises(NameError):
        get_post_processing_service_from_run_name(context=pac_bio_context, run_name=wrong_run_name)

    # THEN an error is raised


def test_get_unprocessed_runs_info_pacbio(
    pac_bio_context: CGConfig, pacbio_unprocessed_runs: list[UnprocessedRunInfo]
):
    """Test that a list of unprocessed runs is returned for Pacbio."""
    # GIVEN a context with a post-processing service for Pacbio
    assert pac_bio_context.post_processing_services.pacbio
    instrument: str = "pacbio"

    # GIVEN that there is an already processed run in the directory
    number_of_runs: int = len(pac_bio_context.run_names_services.pacbio.get_run_names())
    number_unprocessed: int = len(pacbio_unprocessed_runs)
    assert number_of_runs > number_unprocessed

    # WHEN getting the unprocessed runs
    unprocessed_runs: list[UnprocessedRunInfo] = get_unprocessed_runs_info(
        context=pac_bio_context, instrument=instrument
    )

    # THEN the expected unprocessed runs are returned
    assert unprocessed_runs
    assert are_lists_equal(unprocessed_runs, pacbio_unprocessed_runs)
