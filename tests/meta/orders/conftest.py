from pathlib import Path

import pytest

from cg.meta.orders import OrdersAPI
from cg.meta.orders.api import FastqSubmitter
from cg.meta.orders.balsamic_submitter import BalsamicSubmitter
from cg.meta.orders.metagenome_submitter import MetagenomeSubmitter
from cg.meta.orders.microbial_submitter import MicrobialSubmitter
from cg.meta.orders.mip_dna_submitter import MipDnaSubmitter
from cg.meta.orders.mip_rna_submitter import MipRnaSubmitter
from cg.meta.orders.rml_submitter import RmlSubmitter
from cg.meta.orders.ticket_handler import TicketHandler
from cg.meta.orders.tomte_submitter import TomteSubmitter
from cg.models.orders.order import OrderIn, OrderType
from cg.store.store import Store
from tests.apps.orderform.conftest import (
    balsamic_order_to_submit,
    fastq_order_to_submit,
    metagenome_order_to_submit,
    microbial_order_to_submit,
    mip_order_to_submit,
    mip_rna_order_to_submit,
    rml_order_to_submit,
    rnafusion_order_to_submit,
    sarscov2_order_to_submit,
    tomte_order_to_submit,
)
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.osticket import MockOsTicket


@pytest.fixture(scope="session")
def all_orders_to_submit(
    balsamic_order_to_submit: dict,
    fastq_order_to_submit: dict,
    metagenome_order_to_submit: dict,
    microbial_order_to_submit: dict,
    mip_order_to_submit: dict,
    mip_rna_order_to_submit: dict,
    rml_order_to_submit: dict,
    rnafusion_order_to_submit: dict,
    sarscov2_order_to_submit: dict,
) -> dict:
    """Returns a dict of parsed order for each order type."""
    return {
        OrderType.BALSAMIC: OrderIn.parse_obj(balsamic_order_to_submit, project=OrderType.BALSAMIC),
        OrderType.FASTQ: OrderIn.parse_obj(fastq_order_to_submit, project=OrderType.FASTQ),
        OrderType.FLUFFY: OrderIn.parse_obj(rml_order_to_submit, project=OrderType.FLUFFY),
        OrderType.METAGENOME: OrderIn.parse_obj(
            metagenome_order_to_submit, project=OrderType.METAGENOME
        ),
        OrderType.MICROSALT: OrderIn.parse_obj(
            microbial_order_to_submit, project=OrderType.MICROSALT
        ),
        OrderType.MIP_DNA: OrderIn.parse_obj(mip_order_to_submit, project=OrderType.MIP_DNA),
        OrderType.MIP_RNA: OrderIn.parse_obj(mip_rna_order_to_submit, project=OrderType.MIP_RNA),
        OrderType.RML: OrderIn.parse_obj(rml_order_to_submit, project=OrderType.RML),
        OrderType.RNAFUSION: OrderIn.parse_obj(
            rnafusion_order_to_submit, project=OrderType.RNAFUSION
        ),
        OrderType.SARS_COV_2: OrderIn.parse_obj(
            sarscov2_order_to_submit, project=OrderType.SARS_COV_2
        ),
    }


@pytest.fixture
def balsamic_status_data(balsamic_order_to_submit: dict):
    """Parse balsamic order example."""
    project: OrderType = OrderType.BALSAMIC
    order: OrderIn = OrderIn.parse_obj(obj=balsamic_order_to_submit, project=project)
    return BalsamicSubmitter.order_to_status(order=order)


@pytest.fixture
def fastq_status_data(fastq_order_to_submit):
    """Parse fastq order example."""
    project: OrderType = OrderType.FASTQ
    order: OrderIn = OrderIn.parse_obj(obj=fastq_order_to_submit, project=project)
    return FastqSubmitter.order_to_status(order=order)


@pytest.fixture
def metagenome_status_data(metagenome_order_to_submit: dict):
    """Parse metagenome order example."""
    project: OrderType = OrderType.METAGENOME
    order: OrderIn = OrderIn.parse_obj(obj=metagenome_order_to_submit, project=project)

    return MetagenomeSubmitter.order_to_status(order=order)


@pytest.fixture
def microbial_status_data(microbial_order_to_submit: dict):
    """Parse microbial order example."""
    project: OrderType = OrderType.MICROSALT
    order: OrderIn = OrderIn.parse_obj(obj=microbial_order_to_submit, project=project)
    return MicrobialSubmitter.order_to_status(order=order)


@pytest.fixture
def mip_rna_status_data(mip_rna_order_to_submit: dict):
    """Parse rna order example."""
    project: OrderType = OrderType.MIP_RNA
    order: OrderIn = OrderIn.parse_obj(obj=mip_rna_order_to_submit, project=project)
    return MipRnaSubmitter.order_to_status(order=order)


@pytest.fixture
def mip_status_data(mip_order_to_submit: dict):
    """Parse scout order example."""
    project: OrderType = OrderType.MIP_DNA
    order: OrderIn = OrderIn.parse_obj(obj=mip_order_to_submit, project=project)
    return MipDnaSubmitter.order_to_status(order=order)


@pytest.fixture
def rml_status_data(rml_order_to_submit):
    """Parse rml order example."""
    project: OrderType = OrderType.RML
    order: OrderIn = OrderIn.parse_obj(obj=rml_order_to_submit, project=project)
    return RmlSubmitter.order_to_status(order=order)


@pytest.fixture
def tomte_status_data(tomte_order_to_submit: dict):
    """Parse TOMTE order example."""
    project: OrderType = OrderType.TOMTE
    order: OrderIn = OrderIn.parse_obj(obj=tomte_order_to_submit, project=project)
    return TomteSubmitter.order_to_status(order=order)


@pytest.fixture(scope="function")
def orders_api(base_store, osticket: MockOsTicket, lims_api: MockLimsAPI):
    return OrdersAPI(lims=lims_api, status=base_store, osticket=osticket)


@pytest.fixture
def ticket_handler(store: Store, osticket: MockOsTicket) -> TicketHandler:
    return TicketHandler(status_db=store, osticket_api=osticket)
