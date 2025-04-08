"""Store fixtures for the order services tests."""

import pytest

from cg.models.orders.constants import OrderType
from cg.services.orders.storing.constants import MAF_ORDER_ID
from cg.store.models import ApplicationVersion, Customer, Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def store_to_submit_and_validate_orders(
    store: Store, helpers: StoreHelpers, customer_id: str
) -> Store:
    app_tags: dict[str, list[OrderType]] = {
        "PANKTTR100": [OrderType.BALSAMIC],
        "PANKTTR020": [OrderType.BALSAMIC],
        "WGSPCFC030": [OrderType.FASTQ, OrderType.MIP_DNA],
        "RMLP15R100": [OrderType.FLUFFY, OrderType.RML],
        "RMLP15R200": [OrderType.FLUFFY, OrderType.RML],
        "RMLP15R400": [OrderType.FLUFFY, OrderType.RML],
        "RMLP15R500": [OrderType.FLUFFY, OrderType.RML],
        "METPCFR030": [OrderType.METAGENOME],
        "METWPFR030": [OrderType.METAGENOME, OrderType.TAXPROFILER],
        "MWRNXTR003": [OrderType.MICROBIAL_FASTQ, OrderType.MICROSALT],
        "MWXNXTR003": [OrderType.MICROSALT],
        "VWGNXTR001": [OrderType.MICROSALT],
        "WGSWPFC030": [OrderType.MIP_DNA],
        "RNAPOAR025": [OrderType.MIP_RNA, OrderType.RNAFUSION, OrderType.TOMTE],
        "LWPBELB070": [OrderType.PACBIO_LONG_READ],
        "VWGDPTR001": [OrderType.SARS_COV_2],
    }
    for tag, orders in app_tags.items():
        application_version: ApplicationVersion = helpers.ensure_application_version(
            store=store, application_tag=tag
        )
        application_version.application.order_types = orders
    customer: Customer = helpers.ensure_customer(store=store, customer_id=customer_id)
    helpers.ensure_user(store=store, customer=customer)
    helpers.ensure_panel(store=store, panel_abbreviation="AID")
    helpers.ensure_panel(store=store, panel_abbreviation="Ataxi")
    helpers.ensure_panel(store=store, panel_abbreviation="IEM")
    helpers.ensure_panel(store=store, panel_abbreviation="OMIM-AUTO")
    order = Order(customer_id=1, id=MAF_ORDER_ID, ticket_id=100000000)
    store.add_item_to_store(order)
    bed = store.add_bed("GIcfDNA")
    store.add_item_to_store(bed)
    store.commit_to_store()
    return store
