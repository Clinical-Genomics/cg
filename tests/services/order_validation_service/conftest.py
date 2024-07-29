import pytest

from cg.constants.constants import GenomeVersion, Workflow
from cg.models.orders.sample_base import ContainerEnum, SexEnum, StatusEnum
from cg.services.order_validation_service.workflows.tomte.constants import (
    TomteDeliveryType,
)
from cg.services.order_validation_service.workflows.tomte.models.case import TomteCase
from cg.services.order_validation_service.workflows.tomte.models.order import TomteOrder
from cg.services.order_validation_service.workflows.tomte.models.sample import (
    TomteSample,
)


def create_sample(id: int) -> TomteSample:
    return TomteSample(
        name=f"name{id}",
        application="application",
        container=ContainerEnum.plate,
        require_qc_ok=True,
        reference_genome=GenomeVersion.hg19,
        sex=SexEnum.female,
        source="source",
        status=StatusEnum.affected,
        subject_id="subject1",
        well_position=f"A:{id}",
    )


def create_case(samples: list[TomteSample]) -> TomteCase:
    return TomteCase(
        name="name",
        data_delivery=TomteDeliveryType.FASTQ,
        panels=[],
        samples=samples,
    )


def create_order(cases: list[TomteCase]) -> TomteOrder:
    return TomteOrder(
        connect_to_ticket=True,
        delivery_type=TomteDeliveryType.FASTQ,
        name="order_name",
        ticket_number="#12345",
        workflow=Workflow.BALSAMIC,
        user_id=1,
        customer="customer",
        cases=cases,
    )


@pytest.fixture
def valid_case() -> TomteCase:
    sample_1: TomteSample = create_sample(1)
    sample_2: TomteSample = create_sample(2)
    return create_case([sample_1, sample_2])


@pytest.fixture
def case_with_samples_in_same_well() -> TomteCase:
    sample_1: TomteSample = create_sample(1)
    sample_2: TomteSample = create_sample(1)
    return create_case([sample_1, sample_2])


@pytest.fixture
def valid_order(valid_case: TomteCase) -> TomteOrder:
    return create_order([valid_case])


@pytest.fixture
def order_with_samples_in_same_well(case_with_samples_in_same_well: TomteCase) -> TomteOrder:
    return create_order([case_with_samples_in_same_well])
