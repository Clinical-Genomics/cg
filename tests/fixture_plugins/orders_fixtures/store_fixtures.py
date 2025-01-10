"""Store fixtures for the order services tests."""

import pytest

from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.constants import OrderType
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.mip_dna.models.order import MipDnaOrder
from cg.store.models import Application
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


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
def store_with_rml_applications(store: Store, helpers: StoreHelpers) -> Store:
    app_tags: list[str] = ["RMLP15R100", "RMLP15R200", "RMLP15R400", "RMLP15R500"]
    for tag in app_tags:
        helpers.ensure_application_version(
            store=store,
            application_tag=tag,
            prep_category=SeqLibraryPrepCategory.READY_MADE_LIBRARY,
        )
    helpers.ensure_customer(store=store, customer_id="cust000")
    return store


@pytest.fixture
def metagenome_storing_store(base_store: Store, helpers: StoreHelpers) -> Store:
    metagenome_application: Application = helpers.ensure_application_version(
        store=base_store, application_tag="METPCFR030"
    ).application
    metagenome_application.order_types = [OrderType.METAGENOME]
    metagenome_application: Application = helpers.ensure_application_version(
        store=base_store, application_tag="METWPFR030"
    ).application
    metagenome_application.order_types = [OrderType.METAGENOME]
    customer = base_store.get_customer_by_internal_id("cust000")
    helpers.ensure_user(store=base_store, customer=customer)
    return base_store


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
