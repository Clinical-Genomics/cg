import pytest

from cg.constants.constants import GenomeVersion, Workflow
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.constants import MINIMUM_VOLUME
from cg.services.order_validation_service.workflows.balsamic.constants import BalsamicDeliveryType
from cg.services.order_validation_service.workflows.balsamic.models.case import BalsamicCase
from cg.services.order_validation_service.workflows.balsamic.models.order import BalsamicOrder
from cg.services.order_validation_service.workflows.balsamic.models.sample import BalsamicSample


def create_sample(id: int) -> BalsamicSample:
    return BalsamicSample(
        name=f"name{id}",
        application="PANKTTR020",
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
        workflow=Workflow.BALSAMIC,
        user_id=1,
        customer="cust000",
        cases=cases,
    )


@pytest.fixture
def valid_order() -> BalsamicOrder:
    sample = create_sample(1)
    case = create_case([sample])
    return create_order([case])
