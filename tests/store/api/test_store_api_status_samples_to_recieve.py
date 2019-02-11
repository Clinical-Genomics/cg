"""This file tests the samples_to_recieve part of the status api"""

from cg.store import Store


def test_samples_to_receive_external(sample_store: Store):
    """Test that we can get the external samples to be received"""

    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding external samples to receive
    external_query = sample_store.samples_to_recieve(external=True)
    assert external_query.count() == 1
    first_sample = external_query.first()
    assert first_sample.application_version.application.is_external is True
    assert first_sample.received_at is None


def test_samples_to_receive_internal(sample_store: Store):
    """Test that we can get the internal samples to be received"""

    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding which samples are in queue to receive
    assert sample_store.samples_to_recieve().count() == 1
    first_sample = sample_store.samples_to_recieve().first()
    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None
