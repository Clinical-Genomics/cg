import pytest

from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, PriorityEnum, SexEnum
from cg.services.order_validation_service.constants import ElutionBuffer
from cg.services.order_validation_service.workflows.fastq.models.order import FastqOrder
from cg.services.order_validation_service.workflows.microbial_fastq.constants import (
    MicrobialFastqDeliveryType,
)
from cg.services.order_validation_service.workflows.microbial_fastq.models.order import (
    MicrobialFastqOrder,
)
from cg.services.order_validation_service.workflows.microbial_fastq.models.sample import (
    MicrobialFastqSample,
)
from cg.services.order_validation_service.workflows.pacbio_long_read.constants import (
    PacbioDeliveryType,
)
from cg.services.order_validation_service.workflows.pacbio_long_read.models.order import PacbioOrder
from cg.services.order_validation_service.workflows.pacbio_long_read.models.sample import (
    PacbioSample,
)


def create_pacbio_sample(id: int) -> PacbioSample:
    return PacbioSample(
        application="LWPBELB070",
        comment="",
        container=ContainerEnum.plate,
        container_name="Pacbio plate",
        name=f"fastq-sample-{id}",
        volume=54,
        concentration_ng_ul=30,
        priority=PriorityEnum.priority,
        quantity=54,
        require_qc_ok=True,
        sex=SexEnum.male,
        source="blood",
        subject_id=f"pacbio-subject-{id}",
        well_position=f"A:{id}",
        tumour=False,
    )


@pytest.fixture
def valid_pacbio_order(ticket_id: str) -> PacbioOrder:
    sample_1: PacbioSample = create_pacbio_sample(1)
    sample_2: PacbioSample = create_pacbio_sample(2)
    sample_3: PacbioSample = create_pacbio_sample(3)
    samples = [sample_1, sample_2, sample_3]
    order = PacbioOrder(
        customer="cust000",
        project_type=OrderType.PACBIO_LONG_READ,
        user_id=0,
        delivery_type=PacbioDeliveryType.BAM,
        samples=samples,
        name="PacbioOrder",
    )
    order._generated_ticket_id = int(ticket_id)
    return order


@pytest.fixture
def fastq_order(fastq_order_to_submit: dict) -> FastqOrder:
    fastq_order = FastqOrder.model_validate(fastq_order_to_submit)
    fastq_order._generated_ticket_id = 123456
    return fastq_order


def create_microbial_fastq_sample(id: int) -> MicrobialFastqSample:
    return MicrobialFastqSample(
        application="MWRNXTR003",
        comment="",
        container=ContainerEnum.tube,
        container_name="Fastq tube",
        name=f"microfastq-sample-{id}",
        volume=54,
        elution_buffer=ElutionBuffer.WATER,
        priority=PriorityEnum.priority,
        quantity=54,
        require_qc_ok=True,
    )


@pytest.fixture
def valid_microbial_fastq_order(ticket_id: str) -> MicrobialFastqOrder:
    sample_1: MicrobialFastqSample = create_microbial_fastq_sample(1)
    sample_2: MicrobialFastqSample = create_microbial_fastq_sample(2)
    sample_3: MicrobialFastqSample = create_microbial_fastq_sample(3)
    order = MicrobialFastqOrder(
        customer="cust000",
        project_type=OrderType.MICROBIAL_FASTQ,
        user_id=0,
        delivery_type=MicrobialFastqDeliveryType.FASTQ,
        samples=[sample_1, sample_2, sample_3],
        name="MicrobialFastqOrder",
    )
    order._generated_ticket_id = ticket_id
    return order
