import pytest

from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum
from cg.services.orders.validation.constants import MINIMUM_VOLUME, ElutionBuffer, ExtractionMethod
from cg.services.orders.validation.workflows.microsalt.constants import MicrosaltDeliveryType
from cg.services.orders.validation.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.orders.validation.workflows.microsalt.models.sample import MicrosaltSample
from cg.store.models import Application
from cg.store.store import Store


def create_microsalt_sample(id: int) -> MicrosaltSample:
    return MicrosaltSample(
        name=f"name{id}",
        application="MWRNXTR003",
        container=ContainerEnum.plate,
        container_name="ContainerName",
        elution_buffer=ElutionBuffer.WATER,
        extraction_method=ExtractionMethod.MAELSTROM,
        organism="C. jejuni",
        priority=PriorityEnum.standard,
        require_qc_ok=True,
        reference_genome="NC_00001",
        well_position=f"A:{id}",
        volume=MINIMUM_VOLUME,
    )


def create_microsalt_order(samples: list[MicrosaltSample]) -> MicrosaltOrder:
    return MicrosaltOrder(
        connect_to_ticket=True,
        delivery_type=MicrosaltDeliveryType.FASTQ_QC,
        name="order_name",
        ticket_number="#12345",
        project_type=OrderType.MICROSALT,
        user_id=1,
        customer="cust000",
        samples=samples,
    )


@pytest.fixture
def valid_microsalt_order() -> MicrosaltOrder:
    sample_1: MicrosaltSample = create_microsalt_sample(1)
    sample_2: MicrosaltSample = create_microsalt_sample(2)
    sample_3: MicrosaltSample = create_microsalt_sample(3)
    return create_microsalt_order([sample_1, sample_2, sample_3])


@pytest.fixture
def sample_with_non_compatible_application() -> MicrosaltSample:
    sample: MicrosaltSample = create_microsalt_sample(1)
    sample.application = "WGSPCFC030"
    return sample


@pytest.fixture
def archived_application(base_store: Store) -> Application:
    return base_store.add_application(
        tag="archived_application",
        prep_category="mic",
        description="This is an archived_application",
        percent_kth=100,
        percent_reads_guaranteed=90,
        is_archived=True,
    )


@pytest.fixture
def order_with_samples_in_same_well() -> MicrosaltOrder:
    sample_1: MicrosaltSample = create_microsalt_sample(1)
    sample_2: MicrosaltSample = create_microsalt_sample(1)
    return create_microsalt_order([sample_1, sample_2])
