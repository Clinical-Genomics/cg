"""Test delivery API methods."""

from cg.meta.delivery.delivery import DeliveryAPI
from cg.models.cg_config import CGConfig
from cg.store.models import Sample
from cg.store.store import Store


def test_convert_files_to_delivery_files():
    """Test Housekeeper file conversion to delivery files."""


def test_is_sample_deliverable(delivery_context_microsalt: CGConfig, sample_id: str):
    """Test that a sample is deliverable."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a sample id with enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id)

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample)

    # THEN the sample should be deliverable
    assert is_deliverable


def test_is_sample_deliverable_false(
    delivery_context_microsalt: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a sample is not deliverable."""

    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a sample without enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id_not_enough_reads)

    # WHEN evaluating if sample is deliverable
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample)

    # THEN the sample should not be deliverable
    assert not is_deliverable


def test_is_sample_deliverable_force(
    delivery_context_microsalt: CGConfig, sample_id_not_enough_reads: str
):
    """Test that a non-deliverable sample is deliverable with a force flag."""
    # GIVEN a delivery context
    delivery_api: DeliveryAPI = delivery_context_microsalt.delivery_api
    status_db: Store = delivery_context_microsalt.status_db

    # GIVEN a rare disease sample without enough reads
    sample: Sample = status_db.get_sample_by_internal_id(sample_id_not_enough_reads)

    # WHEN evaluating if sample is deliverable with a force flag
    is_deliverable: bool = delivery_api.is_sample_deliverable(sample=sample, force=True)

    # THEN the sample should be deliverable
    assert is_deliverable
