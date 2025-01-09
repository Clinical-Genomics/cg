import pytest

from cg.models.orders.constants import OrderType
from cg.services.order_validation_service.order_validation_service import OrderValidationService
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.fluffy.models.order import FluffyOrder
from cg.services.order_validation_service.workflows.metagenome.models.order import MetagenomeOrder
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder
from cg.services.order_validation_service.workflows.mip_rna.models.order import MipRnaOrder
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.orders.store_order_services.instantiations.store_metagenome_order import (
    StoreMetagenomeOrderService,
)
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def metagenome_order(
    metagenome_order_to_submit: dict, store_metagenome_order_service: StoreMetagenomeOrderService
) -> MetagenomeOrder:
    """Parse metagenome order example."""
    order_validation_service = OrderValidationService(store_metagenome_order_service.status_db)
    order: MetagenomeOrder = order_validation_service.parse_and_validate(
        raw_order=metagenome_order_to_submit, order_type=OrderType.METAGENOME
    )
    order._generated_ticket_id = 123456
    return order


@pytest.fixture
def valid_rml_order(rml_order_to_submit: dict, ticket_id_as_int: int) -> RmlOrder:
    """Parse rml order example."""
    rml_order = RmlOrder.model_validate(rml_order_to_submit)
    rml_order._generated_ticket_id = ticket_id_as_int
    return rml_order


@pytest.fixture
def valid_fluffy_order(fluffy_order_to_submit: dict, ticket_id_as_int: int) -> FluffyOrder:
    """Parse Fluffy order example."""
    fluffy_order = FluffyOrder.model_validate(fluffy_order_to_submit)
    fluffy_order._generated_ticket_id = ticket_id_as_int
    return fluffy_order


@pytest.fixture
def fastq_order(fastq_order_to_submit: dict) -> FastqOrder:
    fastq_order = FastqOrder.model_validate(fastq_order_to_submit)
    fastq_order._generated_ticket_id = 123456
    return fastq_order


@pytest.fixture
def mip_rna_order(mip_rna_order_to_submit: dict) -> MipRnaOrder:
    mip_rna_order_to_submit["user_id"] = 1
    mip_rna_order = MipRnaOrder.model_validate(mip_rna_order_to_submit)
    for case_index, sample_index, sample in mip_rna_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    mip_rna_order._generated_ticket_id = 123456
    return mip_rna_order


@pytest.fixture
def mip_dna_order(mip_dna_order_to_submit: dict) -> MipDnaOrder:
    mip_dna_order_to_submit["user_id"] = 1
    mip_dna_order = MipDnaOrder.model_validate(mip_dna_order_to_submit)
    for case_index, sample_index, sample in mip_dna_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    mip_dna_order._generated_ticket_id = 123456
    return mip_dna_order


@pytest.fixture
def mip_dna_submit_store(
    base_store: Store, mip_dna_order: MipDnaOrder, helpers: StoreHelpers
) -> Store:
    for _, _, sample in mip_dna_order.enumerated_new_samples:
        if not base_store.get_application_by_tag(sample.application):
            application_version = helpers.ensure_application_version(
                store=base_store, application_tag=sample.application
            )
            base_store.session.add(application_version)
    base_store.session.commit()
    return base_store


@pytest.fixture
def balsamic_order(balsamic_order_to_submit: dict) -> BalsamicOrder:
    balsamic_order_to_submit["user_id"] = 1
    balsamic_order = BalsamicOrder.model_validate(balsamic_order_to_submit)
    balsamic_order._generated_ticket_id = 123456
    for case_index, sample_index, sample in balsamic_order.enumerated_new_samples:
        sample._generated_lims_id = f"ACC{case_index}-{sample_index}"
    return balsamic_order


@pytest.fixture
def balsamic_submit_store(
    base_store: Store, balsamic_order: BalsamicOrder, helpers: StoreHelpers
) -> Store:
    for _, _, sample in balsamic_order.enumerated_new_samples:
        if not base_store.get_application_by_tag(sample.application):
            application_version = helpers.ensure_application_version(
                store=base_store, application_tag=sample.application
            )
            base_store.session.add(application_version)
    base_store.session.commit()
    return base_store


@pytest.fixture
def microsalt_order(microbial_order_to_submit: dict) -> MicrosaltOrder:
    order = MicrosaltOrder.model_validate(microbial_order_to_submit)
    order._generated_ticket_id = 123456
    return order
