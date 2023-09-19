"""Test for the DownSampleMetaData class."""
from cg.store import Store
from cg.store.models import Family, Sample


def test_downsample_meta_data_pass_pre_flight(
    store_with_multiple_cases_and_samples: Store,
    case_id_with_single_sample: str,
    sample_id_in_single_case: str,
    number_of_reads_in_millions: int,
):
    """Test that the pre-flight checks pass when initialising a DownsampleMetaData class."""
    # GIVEN a store with a sample and a case
    case: Family = store_with_multiple_cases_and_samples.get_case_by_internal_id(
        internal_id=case_id_with_single_sample
    )
    sample: Sample = store_with_multiple_cases_and_samples.get_sample_by_internal_id(
        internal_id=sample_id_in_single_case
    )

    # GIVEN that the sample has enough reads to down sample
    assert sample.sequencing_reads > number_of_reads_in_millions * 1000000
