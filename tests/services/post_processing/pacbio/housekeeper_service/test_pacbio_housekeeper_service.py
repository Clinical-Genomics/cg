"""Module for the PacBioHousekeeperService tests."""

from cg.services.post_processing.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.post_processing.pacbio.run_data_generator.run_data import PacBioRunData


def test_store_files_in_housekeeper(
    pac_bio_housekeeper_service: PacBioHousekeeperService,
    expected_pac_bio_run_data: PacBioRunData,
    expexted_pac_bio_sample_name: str,
    expected_smrt_cell_bundle_name: str,
):
    # GIVEN a PacBioRunData object and a PacBioHousekeeperService

    # WHEN storing files in Housekeeper
    pac_bio_housekeeper_service.store_files_in_housekeeper(expected_pac_bio_run_data)

    # THEN a SMRT cell bundle is created
    assert pac_bio_housekeeper_service.hk_api.get_latest_bundle_version(
        expected_smrt_cell_bundle_name
    )

    # THEN a sample bundle is created
    assert pac_bio_housekeeper_service.hk_api.get_latest_bundle_version(
        expexted_pac_bio_sample_name
    )
