from unittest.mock import create_autospec

import pytest

from cg.apps.lims import LimsAPI
from cg.constants.constants import CAPTUREKIT_CANCER_OPTIONS, GenomeVersion
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, SexEnum, StatusEnum
from cg.services.orders.validation.constants import MINIMUM_VOLUME, ElutionBuffer
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_type_maps import ORDER_TYPE_RULE_SET_MAP, RuleSet
from cg.services.orders.validation.order_types.balsamic.constants import BalsamicDeliveryType
from cg.services.orders.validation.order_types.balsamic.models.case import BalsamicCase
from cg.services.orders.validation.order_types.balsamic.models.order import BalsamicOrder
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.service import OrderValidationService
from cg.store.models import Application, Customer, User
from cg.store.store import Store


def create_sample(id: int) -> BalsamicSample:
    return BalsamicSample(
        name=f"name{id}",
        application="PANKTTR020",
        capture_kit=CAPTUREKIT_CANCER_OPTIONS[0],
        container=ContainerEnum.plate,
        container_name="ContainerName",
        control=ControlEnum.not_control,
        elution_buffer=ElutionBuffer.WATER,
        require_qc_ok=True,
        reference_genome=GenomeVersion.HG19,
        sex=SexEnum.female,
        source="source",
        status=StatusEnum.affected,
        subject_id=f"subject{id}",
        well_position=f"A:{id}",
        volume=MINIMUM_VOLUME,
        tumour=False,
    )


def create_case(samples: list[BalsamicSample | ExistingSample]) -> BalsamicCase:
    return BalsamicCase(
        name="name",
        samples=samples,
    )


def create_order(cases: list[BalsamicCase]) -> BalsamicOrder:
    order = BalsamicOrder(
        delivery_type=BalsamicDeliveryType.FASTQ_ANALYSIS,
        name="order_name",
        project_type=OrderType.BALSAMIC,
        customer="cust000",
        cases=cases,
    )
    order._user_id = 1
    order._generated_ticket_id = 12345
    return order


@pytest.fixture
def valid_order() -> BalsamicOrder:
    sample = create_sample(1)
    case = create_case([sample])
    return create_order([case])


@pytest.fixture
def balsamic_application(base_store: Store) -> Application:
    application: Application = base_store.add_application(
        tag="PANKTTR020",
        prep_category="tgs",
        description="This is an application which is compatible with balsamic",
        percent_kth=100,
        percent_reads_guaranteed=90,
        sample_concentration_minimum=50,
        sample_concentration_maximum=250,
    )
    application.order_types = [OrderType.BALSAMIC]
    base_store.session.add(application)
    base_store.commit_to_store()
    return application


@pytest.fixture
def balsamic_validation_service(
    base_store: Store,
    balsamic_application: Application,
) -> OrderValidationService:
    customer: Customer = base_store.get_customer_by_internal_id("cust000")
    user: User = base_store.add_user(customer=customer, email="mail@email.com", name="new user")
    base_store.add_item_to_store(user)
    base_store.add_item_to_store(balsamic_application)
    bed = base_store.add_bed("GIcfDNA")
    base_store.add_item_to_store(bed)
    base_store.commit_to_store()
    return OrderValidationService(lims_api=create_autospec(LimsAPI), store=base_store)


@pytest.fixture
def balsamic_rule_set() -> RuleSet:
    return ORDER_TYPE_RULE_SET_MAP[OrderType.BALSAMIC]


@pytest.fixture
def another_balsamic_sample() -> BalsamicSample:
    return create_sample(2)


@pytest.fixture
def a_third_balsamic_sample() -> BalsamicSample:
    return create_sample(3)
