from cg.constants import DataDelivery, Workflow
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.sample_base import SexEnum
from cg.services.order_validation_service.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.services.orders.store_order_services.implementations.store_pacbio_order_service import (
    StorePacBioOrderService,
)
from cg.store.models import Case, Order, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


def test_store_order_data_in_status_db(
    base_store: Store,
    valid_pacbio_order: PacbioOrder,
    store_pacbio_order_service: StorePacBioOrderService,
    helpers: StoreHelpers,
):
    """Test that a PacBio order is stored in the database."""
    # GIVEN a valid Pacbio order and a Pacbio store service

    # GIVEN a basic store with no samples, cases nor orders
    assert not base_store._get_query(table=Sample).first()
    assert base_store._get_query(table=Case).count() == 0
    assert base_store._get_query(table=Order).count() == 0

    # GIVEN that a Pacbio application exists in the store
    helpers.ensure_application_version(
        store=base_store,
        application_tag="LWPBELB070",
        prep_category=SeqLibraryPrepCategory.WHOLE_GENOME_SEQUENCING,
    )

    # WHEN storing the order
    new_samples: list[Sample] = store_pacbio_order_service.store_order_data_in_status_db(
        order=valid_pacbio_order
    )

    # THEN it should store the order
    assert base_store._get_query(table=Order).count() == 1

    # THEN it should store the samples and create a case for each sample
    assert len(new_samples) == 3
    assert len(base_store._get_query(table=Sample).all()) == 3
    assert base_store._get_query(table=Case).count() == 3
    for new_sample in new_samples:
        # THEN the sample sex should be stored
        assert new_sample.sex == SexEnum.male
        # THEN the sample should have a relationship with a case
        assert len(new_sample.links) == 1
        case_link = new_sample.links[0]
        assert case_link.case in base_store.get_cases()
        # THEN the analysis for the case should be RAW_DATA
        assert case_link.case.data_analysis == Workflow.RAW_DATA
        # THEN the delivery type for the case should be BAM or NO_DELIVERY
        assert case_link.case.data_delivery in [DataDelivery.BAM, DataDelivery.NO_DELIVERY]
