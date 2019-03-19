

def test_samples_to_receive_external(sample_store):

    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding external samples to receive
    external_query = sample_store.samples_to_recieve(external=True)
    assert external_query.count() == 1
    first_sample = external_query.first()
    assert first_sample.application_version.application.is_external is True
    assert first_sample.received_at is None


def test_samples_to_receive_internal(sample_store):

    # GIVEN a store with samples in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.received_at]) > 1

    # WHEN finding which samples are in queue to receive
    assert sample_store.samples_to_recieve().count() == 1
    first_sample = sample_store.samples_to_recieve().first()
    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None


def test_samples_to_sequence(sample_store):

    # GIVEN a store with sample in a mix of states
    assert sample_store.samples().count() > 1
    assert len([sample for sample in sample_store.samples() if sample.sequenced_at]) >= 1

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples = sample_store.samples_to_sequence()

    # THEN it should list the received and partly sequenced samples
    assert sequence_samples.count() == 2
    assert {sample.name for sample in sequence_samples} == set(['sequenced-partly', 'received-prepared'])
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == 'sequenced-partly':
            assert sample.reads > 0
