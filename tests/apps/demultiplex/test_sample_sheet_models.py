from cg.apps.demultiplex.sample_sheet.sample_models import FlowCellSampleBCLConvert
from cg.apps.demultiplex.sample_sheet.sample_sheet_models import SampleSheet


def test_get_non_pooled_samples_when_no_samples():
    # GIVEN a sample sheet with no samples
    sample_sheet = SampleSheet(samples=[])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN no samples should be returned
    assert not samples


def test_get_non_pooled_samples_when_multiple_samples_same_lane():
    # GIVEN a sample sheet with multiple samples on the same lane
    sample1 = FlowCellSampleBCLConvert(lane=1, sample_id="ACC123", index="A")
    sample2 = FlowCellSampleBCLConvert(lane=1, sample_id="ACC456", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN no samples should be returned
    assert not samples


def test_get_non_pooled_samples_when_single_sample_one_lane():
    # GIVEN a sample sheet with a single sample on one lane
    non_pooled_sample = FlowCellSampleBCLConvert(lane=1, sample_id="ACC123", index="A")
    sample_sheet = SampleSheet(samples=[non_pooled_sample])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN the non pooled sample should be returned
    assert samples == [non_pooled_sample]


def test_get_non_pooled_samples_when_multiple_lanes_one_single():
    # GIVEN a sample sheet with multiple lanes and a single sample in one lane
    sample1 = FlowCellSampleBCLConvert(lane=1, sample_id="ACC123", index="A")
    sample2 = FlowCellSampleBCLConvert(lane=1, sample_id="ACC456", index="A")
    non_pooled_sample = FlowCellSampleBCLConvert(lane=2, sample_id="ACC789", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2, non_pooled_sample])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN the non pooled sample should be returned
    assert samples == [non_pooled_sample]
