from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSample
from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet
from cg.apps.demultiplex.sample_sheet.sample_sheet_validator import SampleSheetValidator
from cg.apps.demultiplex.sample_sheet.validators import is_valid_sample_internal_id


def test_get_non_pooled_samples_when_no_samples():
    # GIVEN a sample sheet with no samples
    sample_sheet = SampleSheet(samples=[])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN no samples should be returned
    assert not samples


def test_get_non_pooled_samples_when_multiple_samples_same_lane():
    # GIVEN a sample sheet with multiple samples on the same lane
    sample1 = FlowCellSample(lane=1, sample_id="ACC123", index="A")
    sample2 = FlowCellSample(lane=1, sample_id="ACC456", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN no samples should be returned
    assert not samples


def test_get_non_pooled_samples_when_single_sample_one_lane():
    # GIVEN a sample sheet with a single sample on one lane
    non_pooled_sample = FlowCellSample(lane=1, sample_id="ACC123", index="A")
    sample_sheet = SampleSheet(samples=[non_pooled_sample])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN the non pooled sample should be returned
    assert samples == [non_pooled_sample]


def test_get_non_pooled_samples_when_multiple_lanes_one_single():
    # GIVEN a sample sheet with multiple lanes and a single sample in one lane
    sample1 = FlowCellSample(lane=1, sample_id="ACC123", index="A")
    sample2 = FlowCellSample(lane=1, sample_id="ACC456", index="A")
    non_pooled_sample = FlowCellSample(lane=2, sample_id="ACC789", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2, non_pooled_sample])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN the non pooled sample should be returned
    assert samples == [non_pooled_sample]


def test_get_sample_internal_ids_from_sample_sheet(
    sample_sheet_validator: SampleSheetValidator,
    novaseq_6000_post_1_5_kits_sample_sheet_object: SampleSheet,
):
    """Test that getting sample internal ids from a sample sheet returns a unique list of strings."""

    # GIVEN a sample sheet with only valid samples

    # WHEN getting the valid sample internal ids
    sample_internal_ids: list[str] = novaseq_6000_post_1_5_kits_sample_sheet_object.get_sample_ids()

    # THEN the returned value is a list
    assert isinstance(sample_internal_ids, list)
    # THEN the list contains strings
    assert isinstance(sample_internal_ids[0], str)
    # THEN the sample internal ids are unique
    assert len(sample_internal_ids) == len(set(sample_internal_ids))
    # THEN the sample internal ids are the expected ones
    for sample_internal_id in sample_internal_ids:
        assert is_valid_sample_internal_id(sample_internal_id=sample_internal_id) is True
