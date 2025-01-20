from cg.constants import DataDelivery, Workflow
from cg.models.orders.sample_base import SexEnum
from cg.services.orders.storing.implementations.pacbio_order_service import StorePacBioOrderService
from cg.services.orders.validation.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.store.models import Case, Order, Sample
from cg.store.store import Store


def test_store_pacbio_order_data_in_status_db(
    store_to_submit_and_validate_orders: Store,
    pacbio_order: PacbioOrder,
    store_pacbio_order_service: StorePacBioOrderService,
):
    """Test that a PacBio order is stored in the database."""
    # GIVEN a valid Pacbio order and a Pacbio store service

    # GIVEN a basic store with no samples, cases and only a MAF order
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 0
    assert store_to_submit_and_validate_orders._get_query(table=Order).count() == 1

    # WHEN storing the order
    new_samples: list[Sample] = store_pacbio_order_service.store_order_data_in_status_db(
        order=pacbio_order
    )

    # THEN it should store the order
    assert store_to_submit_and_validate_orders._get_query(table=Order).count() == 2

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 3
    assert len(store_to_submit_and_validate_orders._get_query(table=Sample).all()) == 3
    assert store_to_submit_and_validate_orders._get_query(table=Case).count() == 3
    for new_sample in new_samples:
        # THEN the sample sex should be stored
        assert new_sample.sex == SexEnum.male
        # THEN the sample should have a relationship with a case
        assert len(new_sample.links) == 1
        case_link = new_sample.links[0]
        assert case_link.case in store_to_submit_and_validate_orders.get_cases()
        # THEN the analysis for the case should be RAW_DATA
        assert case_link.case.data_analysis == Workflow.RAW_DATA
        # THEN the delivery type for the case should be BAM or NO_DELIVERY
        assert case_link.case.data_delivery in [DataDelivery.BAM, DataDelivery.NO_DELIVERY]
