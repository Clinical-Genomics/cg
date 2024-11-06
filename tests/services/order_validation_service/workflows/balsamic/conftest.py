import pytest

from cg.constants.constants import CAPTUREKIT_CANCER_OPTIONS, GenomeVersion
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import MINIMUM_VOLUME
from cg.services.order_validation_service.workflows.balsamic.constants import (
    BalsamicDeliveryType,
)
from cg.services.order_validation_service.workflows.balsamic.models.case import (
    BalsamicCase,
)
from cg.services.order_validation_service.workflows.balsamic.models.order import (
    BalsamicOrder,
)
from cg.services.order_validation_service.workflows.balsamic.models.sample import (
    BalsamicSample,
)
from cg.services.order_validation_service.workflows.balsamic.validation_service import (
    BalsamicValidationService,
)
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
        require_qc_ok=True,
        reference_genome=GenomeVersion.HG19,
        sex=SexEnum.female,
        source="source",
        status=StatusEnum.affected,
        subject_id=f"subject{id}",
        well_position=f"A:{id}",
        volume=MINIMUM_VOLUME,
        is_tumour=False,
    )


def create_case(samples: list[BalsamicSample]) -> BalsamicCase:
    return BalsamicCase(
        name="name",
        samples=samples,
    )


def create_order(cases: list[BalsamicCase]) -> BalsamicOrder:
    return BalsamicOrder(
        connect_to_ticket=True,
        delivery_type=BalsamicDeliveryType.FASTQ_ANALYSIS,
        name="order_name",
        ticket_number="#12345",
        project_type=OrderType.BALSAMIC,
        user_id=1,
        customer="cust000",
        cases=cases,
    )


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
) -> BalsamicValidationService:
    customer: Customer = base_store.get_customer_by_internal_id("cust000")
    user: User = base_store.add_user(customer=customer, email="mail@email.com", name="new user")
    base_store.session.add(user)
    base_store.session.add(balsamic_application)
    base_store.session.commit()
    return BalsamicValidationService(base_store)
