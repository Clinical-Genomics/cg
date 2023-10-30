"""Test for the DownSampleMetaData class."""


from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.downsample.downsample_data import DownsampleData
from cg.store import Store
from cg.store.models import Family, Sample


def test_downsample_meta_data_pass_pre_flight(
    store_with_case_and_sample_with_reads: Store,
    downsample_hk_api: HousekeeperAPI,
    downsample_case_internal_id: str,
    downsample_sample_internal_id_1: str,
    number_of_reads_in_millions: int,
    tmp_path_factory,
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

    # WHEN initialising the DownsampleData class
    tmp_path = tmp_path_factory.mktemp("tmp")

    def return_tmp_dir(path=tmp_path):
        return path

    mock_object = DownsampleData
    mock_object.create_down_sampling_working_directory = return_tmp_dir
    meta_data = DownsampleData(
        status_db=store_with_case_and_sample_with_reads,
        hk_api=downsample_hk_api,
        sample_internal_id=downsample_sample_internal_id_1,
        case_internal_id=downsample_case_internal_id,
        number_of_reads=number_of_reads_in_millions,
    )

    # THEN all necessary models to run the down sample command are created
    assert (
        meta_data.downsampled_sample.internal_id
        == f"{sample.internal_id}_{number_of_reads_in_millions}M"
    )
    assert meta_data.downsampled_sample.reads == number_of_reads_in_millions * 1_000_000
    assert meta_data.downsampled_case.name == f"{case.internal_id}_downsampled"
    assert meta_data.has_enough_reads
