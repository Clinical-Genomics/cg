"""Test delivery API methods."""

from cg.models.cg_config import CGConfig
from cg.store.models import Sample


def test_is_sample_deliverable(raredisease_context: CGConfig, sample_id: str):
    """Test that a sample is deliverable."""

    # GIVEN a rare disease context and a sample with enough reads
    sample: Sample = raredisease_context.status_db.get_sample_by_internal_id(sample_id)

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = raredisease_context.delivery_api.is_sample_deliverable(sample)

    # THEN the sample should be deliverable
    assert is_deliverable


def test_is_sample_deliverable_false(
    raredisease_context: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a sample is not deliverable."""

    # GIVEN a rare disease context and a sample without enough reads
    sample: Sample = raredisease_context.status_db.get_sample_by_internal_id(
        sample_id_not_enough_reads
    )

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = raredisease_context.delivery_api.is_sample_deliverable(sample)

    # THEN the sample should not be deliverable
    assert not is_deliverable


def test_is_sample_deliverable_force(
    raredisease_context: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a sample is deliverable with a force flag."""

    # GIVEN a rare disease context and a sample without enough reads
    sample: Sample = raredisease_context.status_db.get_sample_by_internal_id(
        sample_id_not_enough_reads
    )

    # WHEN evaluating if sample is deliverable with a force flag
    is_deliverable: bool = raredisease_context.delivery_api.is_sample_deliverable(
        sample=sample, force=True
    )

    # THEN the sample should be deliverable
    assert is_deliverable
