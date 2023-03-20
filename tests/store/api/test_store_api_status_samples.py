"""Tests for store API status module related to samples."""

from alchy import Query
from typing import List
from cg.constants import Pipeline, Priority
from cg.constants.subject import PhenotypeStatus
from cg.store import Store
from cg.store.models import Analysis, Application, Family, Sample
from tests.store_helpers import StoreHelpers


def test_samples_to_receive_external(sample_store: Store, helpers: StoreHelpers):
    """Test fetching external sample."""
    # GIVEN a store with a mixture of samples
    assert len(sample_store.get_samples()) > 1

    # WHEN finding external samples to receive
    samples: List[Sample] = sample_store.get_samples_to_receive(external=True)

    # ASSERT that external_query is a list[sample]
    assert isinstance(samples, list)
    # THEN assert that only the external sample is returned
    assert len(samples) == 1

    first_sample = samples[0]
    # THEN assert that the sample is external in database
    assert first_sample.application_version.application.is_external is True
    # THEN assert that the sample is does not have a received at stamp
    assert first_sample.received_at is None


def test_get_all_samples_to_receive_internal(sample_store):
    # GIVEN a store with samples in a mix of states
    assert len(sample_store.get_samples()) > 1
    assert len([sample for sample in sample_store.get_samples() if sample.received_at]) > 1

    # WHEN finding which samples are in queue to receive
    assert len(sample_store.get_samples_to_receive()) == 1
    first_sample = sample_store.get_samples_to_receive()[0]
    assert first_sample.application_version.application.is_external is False
    assert first_sample.received_at is None


def test_samples_to_sequence(sample_store):
    # GIVEN a store with sample in a mix of states
    assert len(sample_store.get_samples()) > 1
    assert len([sample for sample in sample_store.get_samples() if sample.sequenced_at]) >= 1

    # WHEN finding which samples are in queue to be sequenced
    sequence_samples: List[Sample] = sample_store.get_samples_to_sequence()

    # THEN it should list the received and partly sequenced samples
    assert len(sequence_samples) == 2
    assert {sample.name for sample in sequence_samples} == set(
        ["sequenced-partly", "received-prepared"]
    )
    for sample in sequence_samples:
        assert sample.sequenced_at is None
        if sample.name == "sequenced-partly":
            assert sample.reads > 0
