"""Test for the DownSampleMetaData class."""

from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.models.downsample.downsample_data import DownsampleData
from cg.store.models import Sample
from cg.store.store import Store


def test_downsample_meta_data_pass_checks(
    store_with_case_and_sample_with_reads: Store,
    downsample_hk_api: HousekeeperAPI,
    downsample_case_internal_id: str,
    downsample_sample_internal_id_1: str,
    downsample_case_name: str,
    number_of_reads_in_millions: int,
    tmp_path_factory,
):
    """Test that the checks pass when initialising a DownsampleData class."""
    # GIVEN a store with a sample and a case
    assert store_with_case_and_sample_with_reads.get_case_by_internal_id(
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
    meta_data = DownsampleData(
        status_db=store_with_case_and_sample_with_reads,
        hk_api=downsample_hk_api,
        sample_id=downsample_sample_internal_id_1,
        case_id=downsample_case_internal_id,
        number_of_reads=number_of_reads_in_millions,
        case_name=downsample_case_name,
        out_dir=tmp_path_factory.mktemp("tmp"),
    )
    # WHEN the number of reads in millionts is converted to a string
    number_of_reads: str = meta_data.convert_number_of_reads_to_string

    # THEN all necessary models to run the down sample command are created
    assert meta_data.downsampled_sample.internal_id == f"{sample.internal_id}DS{number_of_reads}M"
    assert meta_data.downsampled_sample.reads == number_of_reads_in_millions * 1_000_000
    assert meta_data.downsampled_case.name == f"{downsample_case_name}-downsampled"
