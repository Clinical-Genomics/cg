from unittest.mock import create_autospec

import pytest

from cg.constants.constants import DataDelivery, Workflow
from cg.constants.priority import Priority
from cg.models.orders.sample_base import SexEnum, StatusEnum
from cg.store.models import Application, BedVersion, Case, Customer, Order, Organism, Sample
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


@pytest.fixture
def mock_store_for_raredisease_params_file_creator() -> Store:
    """Fixture to provide a mock store for the params file creator."""
    sample: Sample = create_autospec(Sample)
    sample.internal_id = "raredisease_sample_id"
    sample.application_version.application.analysis_type = "wgs"
    case: Case = create_autospec(Case)
    case.internal_id = "raredisease_case_id"
    case.samples = [sample]
    case.data_analysis = Workflow.RAREDISEASE
    store: Store = create_autospec(Store)
    store.get_case_by_internal_id.return_value = case
    store.get_samples_by_case_id.return_value = [sample]
    store.get_sample_by_internal_id.return_value = sample
    bed_version = create_autospec(BedVersion)
    bed_version.filename = "bed_version_file.bed"
    store.get_bed_version_by_short_name.return_value = bed_version
    return store
