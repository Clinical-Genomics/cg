"""Test for the DownSampleMetaData class."""
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.store import Store
from cg.store.models import Family, Sample


def test_downsample_meta_data_pass_pre_flight(
    store_with_case_and_sample_with_reads: Store,
    downsample_hk_api: HousekeeperAPI,
    downsample_case_internal_id: str,
    downsample_sample_internal_id_1: str,
    number_of_reads_in_millions: int,
):
    """Test that the pre-flight checks pass when initialising a DownsampleMetaData class."""
    # GIVEN a store with a sample and a case
    case: Family = store_with_case_and_sample_with_reads.get_case_by_internal_id(
        internal_id=downsample_case_internal_id
    )
    sample: Sample = store_with_case_and_sample_with_reads.get_sample_by_internal_id(
        internal_id=downsample_sample_internal_id_1
    )

    # GIVEN that the sample has enough reads to down sample
    assert sample.reads > number_of_reads_in_millions * 1_000_000

    # GIVEN a bundle exists in housekeeper for the sample
    assert downsample_hk_api.get_latest_bundle_version(sample.internal_id)
