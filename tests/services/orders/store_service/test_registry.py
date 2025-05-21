import pytest

from cg.models.orders.constants import OrderType
from cg.services.orders.storing.service import StoreOrderService
from cg.services.orders.storing.service_registry import StoringServiceRegistry


@pytest.mark.parametrize(
    "order_type, storing_service_fixture",
    [
        (OrderType.BALSAMIC, "store_generic_order_service"),
        (OrderType.FASTQ, "store_fastq_order_service"),
        (OrderType.FLUFFY, "store_pool_order_service"),
        (OrderType.METAGENOME, "store_metagenome_order_service"),
        (OrderType.MICROBIAL_FASTQ, "store_microbial_fastq_order_service"),
        (OrderType.MICROSALT, "store_microbial_order_service"),
        (OrderType.MIP_DNA, "store_generic_order_service"),
        (OrderType.MIP_RNA, "store_generic_order_service"),
        (OrderType.PACBIO_LONG_READ, "store_pacbio_order_service"),
        (OrderType.RML, "store_pool_order_service"),
        (OrderType.RNAFUSION, "store_generic_order_service"),
        (OrderType.SARS_COV_2, "store_microbial_order_service"),
        (OrderType.TAXPROFILER, "store_taxprofiler_order_service"),
        (OrderType.TOMTE, "store_generic_order_service"),
    ],
    ids=[
        "balsamic",
        "fastq",
        "fluffy",
        "metagenome",
        "microbial_fastq",
        "microbial",
        "mip_dna",
        "mip_rna",
        "pacbio_long_read",
        "rml",
        "rnafusion",
        "sars_cov_2",
        "taxprofiler",
        "tomte",
    ],
)
def test_get_storing_service(
    storing_service_registry: StoringServiceRegistry,
    order_type: OrderType,
    storing_service_fixture: str,
    request: pytest.FixtureRequest,
):
    """Test that getting a storing service returns the correct service for any known order type."""
    # GIVEN a storing service registry

    # WHEN getting a storing service for a known order type
    storing_service: StoreOrderService = storing_service_registry.get_storing_service(order_type)

    # THEN the correct storing service should be returned
    expected_storing_service: StoreOrderService = request.getfixturevalue(storing_service_fixture)
    assert isinstance(storing_service, type(expected_storing_service))


def test_get_storing_registry_unknown_order_type(storing_service_registry: StoringServiceRegistry):
    """Test that getting a storing service for an unknown order type raises a ValueError."""
    # GIVEN a storing service registry

    # WHEN getting a storing service for an unknown order type

    # THEN it should raise a ValueError
    with pytest.raises(ValueError):
        storing_service_registry.get_storing_service(order_type="non_existing_order_type")
