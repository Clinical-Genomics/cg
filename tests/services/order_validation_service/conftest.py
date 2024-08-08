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
from cg.services.order_validation_service.workflows.tomte.validation_service import (
    TomteValidationService,
)
from cg.store.models import Application
from cg.store.store import Store


def create_sample(id: int) -> TomteSample:
    return TomteSample(
        name=f"name{id}",
        application="RNAPOAR100",
        container=ContainerEnum.plate,
        container_name="ContainerName",
        require_qc_ok=True,
        reference_genome=GenomeVersion.HG19,
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
        workflow=Workflow.TOMTE,
        user_id=1,
        customer="customer",
        cases=cases,
    )


@pytest.fixture
def case_with_samples_in_same_well() -> TomteCase:
    sample_1: TomteSample = create_sample(1)
    sample_2: TomteSample = create_sample(1)
    return create_case([sample_1, sample_2])


@pytest.fixture
def sample_with_non_compatible_application() -> TomteSample:
    sample: TomteSample = create_sample(1)
    sample.application = "WGSPCFC030"
    return sample


@pytest.fixture
def archived_application(base_store: Store) -> Application:
    return base_store.add_application(
        tag="archived_application",
        prep_category="wts",
        description="This is an archived_application",
        percent_kth=100,
        percent_reads_guaranteed=90,
        is_archived=True,
    )


@pytest.fixture
def valid_order() -> TomteOrder:
    child: TomteSample = create_sample(1)
    father: TomteSample = create_sample(2)
    mother: TomteSample = create_sample(3)
    grandfather: TomteSample = create_sample(4)
    grandmother: TomteSample = create_sample(5)
    case = create_case([child, father, mother, grandfather, grandmother])
    return create_order([case])


@pytest.fixture
def order_with_samples_in_same_well(case_with_samples_in_same_well: TomteCase) -> TomteOrder:
    return create_order([case_with_samples_in_same_well])


@pytest.fixture
def case_with_samples_with_repeated_names() -> TomteCase:
    sample_1: TomteSample = create_sample(1)
    sample_2: TomteSample = create_sample(1)
    sample_1.name = sample_2.name
    return create_case([sample_1, sample_2])


@pytest.fixture
def order_with_repeated_sample_names(
    case_with_samples_with_repeated_names: TomteCase,
) -> TomteOrder:
    return create_order([case_with_samples_with_repeated_names])


@pytest.fixture
def case() -> TomteCase:
    sample_1: TomteSample = create_sample(1)
    sample_2: TomteSample = create_sample(2)
    return create_case([sample_1, sample_2])


@pytest.fixture
def order_with_repeated_case_names(case: TomteCase) -> TomteOrder:
    return create_order([case, case])


@pytest.fixture
def order_with_invalid_father_sex(case: TomteCase):
    child = case.samples[0]
    father = case.samples[1]
    child.father = father.name
    father.sex = SexEnum.female
    return create_order([case])


@pytest.fixture
def order_with_father_in_wrong_case(case: TomteCase):
    child = case.samples[0]
    father = case.samples[1]
    child.father = father.name
    case.samples = [child]
    return create_order([case])


@pytest.fixture
def order_with_sample_cycle():
    child: TomteSample = create_sample(1)
    father: TomteSample = create_sample(2)
    mother: TomteSample = create_sample(3)
    grandfather: TomteSample = create_sample(4)
    grandmother: TomteSample = create_sample(5)

    child.mother = mother.name
    child.father = father.name

    father.mother = grandmother.name
    father.father = child.name  # Cycle introduced here

    case = create_case([child, father, mother, grandfather, grandmother])
    return create_order([case])


@pytest.fixture
def order_with_siblings_as_parents():
    child: TomteSample = create_sample(1)

    father: TomteSample = create_sample(3)
    mother: TomteSample = create_sample(4)

    grandfather: TomteSample = create_sample(5)
    grandmother: TomteSample = create_sample(6)

    child.father = father.name
    child.mother = mother.name

    father.mother = grandmother.name
    father.father = grandfather.name

    mother.mother = grandmother.name
    mother.father = grandfather.name

    case = create_case([child, father, mother, grandfather, grandmother])
    return create_order([case])


def sample_with_invalid_concentration():
    sample: TomteSample = create_sample(1)
    sample.concentration_ng_ul = 1
    return sample
  
  
def sample_with_missing_well_position():
    sample = create_sample(1)
    sample.well_position = None
    return sample


@pytest.fixture
def application_with_concentration_interval(base_store: Store) -> Application:
    return base_store.add_application(
        tag="RNAPOAR100",
        prep_category="wts",
        description="This is an application with concentration interval",
        percent_kth=100,
        percent_reads_guaranteed=90,
        sample_concentration_minimum=50,
        sample_concentration_maximum=250,
    )


@pytest.fixture
def order_with_invalid_concentration(sample_with_invalid_concentration) -> TomteOrder:
    case = create_case([sample_with_invalid_concentration])
    order = create_order([case])
    order.skip_reception_control = True
    return order

@pytest.fixture
def sample_with_missing_container_name() -> TomteSample:
    sample: TomteSample = create_sample(1)
    sample.container_name = None
    return sample


@pytest.fixture
def tomte_validation_service(base_store: Store) -> TomteValidationService:
    return TomteValidationService(base_store)

