from datetime import datetime

from cg.constants import DataDelivery, Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.order import OrderIn
from cg.models.orders.sample_base import SexEnum
from cg.services.orders.store_order_services.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.store.models import Case, Sample
from cg.store.store import Store


def test_order_to_status(
    pacbio_order_to_submit: dict, store_pacbio_order_service: StorePacBioOrderService
):
    """Test that a PacBio order is parsed correctly."""
    # GIVEN a PacBio order with two samples
    order = OrderIn.parse_obj(pacbio_order_to_submit, OrderType.PACBIO_LONG_READ)

    # WHEN parsing for status
    data = store_pacbio_order_service.order_to_status(order=order)

    # THEN it should pick out samples and relevant information
    assert len(data["samples"]) == 2
    first_sample = data["samples"][0]
    assert first_sample["name"] == "prov1"
    assert first_sample["application"] == "WGSPCFC060"
    assert first_sample["priority"] == "priority"
    assert first_sample["tumour"] is False
    assert first_sample["volume"] == "25"

    # THEN the other sample is a tumour
    assert data["samples"][1]["tumour"] is True


def test_store_order(
    base_store: Store,
    pacbio_status_data: dict,
    ticket_id: str,
    store_pacbio_order_service: StorePacBioOrderService,
):
    """Test that a PacBio order is stored in the database."""
    # GIVEN a basic store with no samples and a PacBio order
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0

    # WHEN storing the order
    new_samples: list[Sample] = store_pacbio_order_service._store_samples_in_statusdb(
        customer_id=pacbio_status_data["customer"],
        order=pacbio_status_data["order"],
        ordered=datetime.now(),
        ticket_id=ticket_id,
        samples=pacbio_status_data["samples"],
    )

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 2
    assert len(base_store._get_query(table=Sample).all()) == 2
    assert base_store._get_query(table=Case).count() == 2
    for new_sample in new_samples:
        assert len(new_sample.links) == 1
        case_link = new_sample.links[0]
        assert case_link.case in base_store.get_cases()
        assert case_link.case.data_analysis
        assert case_link.case.data_delivery in [DataDelivery.BAM, DataDelivery.NO_DELIVERY]

    # THEN the sample sex should be stored
    assert new_samples[0].sex == SexEnum.female

    # THEN the analysis for the case should be RAW_DATA
    assert new_samples[0].links[0].case.data_analysis == Workflow.RAW_DATA
