from cg.apps.demultiplex.sample_sheet.models import FlowCellSample, SampleSheet


def test_get_single_samples_no_samples():
    # GIVEN a sample sheet with no samples
    sample_sheet = SampleSheet(samples=[])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples() == []

    # THEN no samples should be returned
    assert not samples


def test_get_single_samples_multiple_samples_same_lane():
    # GIVEN a sample sheet with multiple samples on the same lane
    sample1 = FlowCellSample(lane=1, sample_id="S1", index="A")
    sample2 = FlowCellSample(lane=1, sample_id="S2", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN no samples should be returned
    assert not samples


def test_get_single_samples_single_sample_one_lane():
    # GIVEN a sample sheet with a single sample on one lane
    sample = FlowCellSample(lane=1, sample_id="S1", index="A")
    sample_sheet = SampleSheet(samples=[sample])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    # THEN the sample should be returned
    assert samples == [sample]


def test_get_single_samples_multiple_lanes_one_single():
    # GIVEN a sample sheet with multiple lanes and a single sample in one lane
    sample1 = FlowCellSample(lane=1, sample_id="S1", index="A")
    sample2 = FlowCellSample(lane=1, sample_id="S2", index="A")
    sample3 = FlowCellSample(lane=2, sample_id="S3", index="A")
    sample_sheet = SampleSheet(samples=[sample1, sample2, sample3])

    # WHEN retrieving any non pooled samples
    samples = sample_sheet.get_non_pooled_samples()

    assert samples == [sample3]
