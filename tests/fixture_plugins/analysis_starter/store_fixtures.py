import pytest

from cg.constants.constants import DataDelivery, Workflow
from cg.constants.priority import Priority
from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.store.models import Application, Case, Customer, Order, Organism, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.fixture
def microsalt_store(base_store: Store, helpers: StoreHelpers) -> Store:
    organism: Organism = base_store.get_all_organisms()[0]
    microsalt_case: Case = helpers.add_case(
        customer_id="cust000",
        data_analysis=Workflow.MICROSALT,
        data_delivery=DataDelivery.ANALYSIS_FILES,
        internal_id="microparakeet",
        name="microsalt-name",
        store=base_store,
        ticket="123456",
    )
    application: Application = base_store.get_application_by_tag("MWRNXTR003")
    customer: Customer = base_store.get_customers()[0]

    microsalt_sample: Sample = base_store.add_sample(
        application_version=application.versions[0],
        customer=customer,
        name="microsalt-sample",
        organism=organism,
        priority=Priority.standard,
        sex=SexEnum.unknown,
    )

    base_store.relate_sample(
        case=microsalt_case, sample=microsalt_sample, status=StatusEnum.unknown
    )
    order: Order = base_store.add_order(customer=customer, ticket_id=1)
    microsalt_case.orders.append(order)
    base_store.add_item_to_store(microsalt_case)
    base_store.add_item_to_store(microsalt_sample)
    base_store.commit_to_store()

    return base_store
