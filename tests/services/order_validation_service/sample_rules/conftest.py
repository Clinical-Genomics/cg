import pytest

from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum, SexEnum
from cg.services.order_validation_service.constants import (
    MINIMUM_VOLUME,
    ElutionBuffer,
    ExtractionMethod,
)
from cg.services.order_validation_service.workflows.fastq.constants import FastqDeliveryType
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.fastq.models.sample import FastqSample
from cg.services.order_validation_service.workflows.microsalt.constants import MicrosaltDeliveryType
from cg.services.order_validation_service.workflows.microsalt.models.order import MicrosaltOrder
from cg.services.order_validation_service.workflows.microsalt.models.sample import MicrosaltSample
from cg.services.order_validation_service.workflows.rml.constants import RmlDeliveryType
from cg.services.order_validation_service.workflows.rml.models.order import RmlOrder
from cg.services.order_validation_service.workflows.rml.models.sample import RmlSample
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


def create_fastq_sample(id: int) -> FastqSample:
    return FastqSample(
        application="WGSPCFC030",
        comment="",
        container=ContainerEnum.tube,
        container_name="Fastq tube",
        name=f"fastq-sample-{id}",
        volume=54,
        concentration_ng_ul=30,
        elution_buffer=ElutionBuffer.WATER,
        priority=PriorityEnum.priority,
        quantity=54,
        require_qc_ok=True,
        sex=SexEnum.male,
        source="blood",
        subject_id=f"fastq-subject-{id}",
    )


@pytest.fixture
def valid_fastq_order() -> FastqOrder:
    sample_1: FastqSample = create_fastq_sample(1)
    sample_2: FastqSample = create_fastq_sample(2)
    sample_3: FastqSample = create_fastq_sample(3)
    samples = [sample_1, sample_2, sample_3]
    return FastqOrder(
        customer="cust000",
        project_type=OrderType.FASTQ,
        user_id=0,
        delivery_type=FastqDeliveryType.FASTQ,
        samples=samples,
        name="FastqOrder",
    )


def create_rml_sample(id: int) -> RmlSample:
    return RmlSample(
        application="RMLCUSR800",
        container=ContainerEnum.plate,
        index_number=4,
        index="Kapa UDI NIPT",
        rml_plate_name="Rml-plate",
        name=f"rml-sample-{id}",
        pool="pool-2",
        pool_concentration=30,
        volume=54,
        priority=PriorityEnum.priority,
        well_position_rml=f"A:{id}",
    )


@pytest.fixture
def valid_rml_order() -> RmlOrder:
    sample_1: RmlSample = create_rml_sample(1)
    sample_2: RmlSample = create_rml_sample(2)
    sample_3: RmlSample = create_rml_sample(3)
    samples = [sample_1, sample_2, sample_3]
    return RmlOrder(
        customer="cust000",
        project_type=OrderType.RML,
        user_id=0,
        delivery_type=RmlDeliveryType.FASTQ,
        samples=samples,
        name="RmlOrder",
    )
