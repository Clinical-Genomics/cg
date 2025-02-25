import pytest

from cg.constants.constants import GenomeVersion
from cg.constants.sequencing import SeqLibraryPrepCategory
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, ControlEnum, SexEnum, StatusEnum
from cg.services.orders.validation.constants import MINIMUM_VOLUME
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.order_type_maps import ORDER_TYPE_RULE_SET_MAP, RuleSet
from cg.services.orders.validation.order_types.tomte.constants import TomteDeliveryType
from cg.services.orders.validation.order_types.tomte.models.case import TomteCase
from cg.services.orders.validation.order_types.tomte.models.order import TomteOrder
from cg.services.orders.validation.order_types.tomte.models.sample import TomteSample
from cg.services.orders.validation.service import OrderValidationService
from cg.store.models import Application, Customer, User
from cg.store.store import Store


def create_tomte_sample(id: int) -> TomteSample:
    return TomteSample(
        name=f"name{id}",
        application="RNAPOAR100",
        container=ContainerEnum.plate,
        container_name="ContainerName",
        control=ControlEnum.not_control,
        require_qc_ok=True,
        reference_genome=GenomeVersion.HG19,
        sex=SexEnum.female,
        source="source",
        status=StatusEnum.affected,
        subject_id="subject1",
        well_position=f"A:{id}",
        volume=MINIMUM_VOLUME,
    )


def create_case(samples: list[TomteSample]) -> TomteCase:
    return TomteCase(
        name="name",
        panels=[],
        samples=samples,
    )


def create_tomte_order(cases: list[TomteCase]) -> TomteOrder:
    order = TomteOrder(
        delivery_type=TomteDeliveryType.FASTQ,
        name="order_name",
        project_type=OrderType.TOMTE,
        customer="cust000",
        cases=cases,
    )
    order._user_id = 1
    order._generated_ticket_id = 123456
    return order


@pytest.fixture
def case_with_samples_in_same_well() -> TomteCase:
    sample_1: TomteSample = create_tomte_sample(1)
    sample_2: TomteSample = create_tomte_sample(1)
    return create_case([sample_1, sample_2])


@pytest.fixture
def sample_with_non_compatible_application() -> TomteSample:
    sample: TomteSample = create_tomte_sample(1)
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
def application_tag_required_buffer() -> str:
    return "WGSWPFR400"


@pytest.fixture
def valid_order() -> TomteOrder:
    child: TomteSample = create_tomte_sample(1)
    father: TomteSample = create_tomte_sample(2)
    mother: TomteSample = create_tomte_sample(3)
    grandfather: TomteSample = create_tomte_sample(4)
    grandmother: TomteSample = create_tomte_sample(5)
    case = create_case([child, father, mother, grandfather, grandmother])
    return create_tomte_order([case])


@pytest.fixture
def order_with_samples_in_same_well(case_with_samples_in_same_well: TomteCase) -> TomteOrder:
    return create_tomte_order([case_with_samples_in_same_well])


@pytest.fixture
def case_with_samples_with_repeated_names() -> TomteCase:
    sample_1: TomteSample = create_tomte_sample(1)
    sample_2: TomteSample = create_tomte_sample(1)
    sample_1.name = sample_2.name
    return create_case([sample_1, sample_2])


@pytest.fixture
def order_with_repeated_sample_names(
    case_with_samples_with_repeated_names: TomteCase,
) -> TomteOrder:
    return create_tomte_order([case_with_samples_with_repeated_names])


@pytest.fixture
def case() -> TomteCase:
    sample_1: TomteSample = create_tomte_sample(1)
    sample_2: TomteSample = create_tomte_sample(2)
    return create_case([sample_1, sample_2])


@pytest.fixture
def order_with_repeated_case_names(case: TomteCase) -> TomteOrder:
    return create_tomte_order([case, case])


@pytest.fixture
def order_with_invalid_father_sex(case: TomteCase):
    child: TomteSample = case.samples[0]
    father: TomteSample = case.samples[1]
    child.father = father.name
    father.sex = SexEnum.female
    return create_tomte_order([case])


@pytest.fixture
def order_with_father_in_wrong_case(case: TomteCase):
    child: TomteSample = case.samples[0]
    father: TomteSample = case.samples[1]
    child.father = father.name
    case.samples = [child]
    return create_tomte_order([case])


@pytest.fixture
def order_with_sample_cycle():
    child: TomteSample = create_tomte_sample(1)
    father: TomteSample = create_tomte_sample(2)
    mother: TomteSample = create_tomte_sample(3)
    grandfather: TomteSample = create_tomte_sample(4)
    grandmother: TomteSample = create_tomte_sample(5)

    child.mother = mother.name
    child.father = father.name

    father.mother = grandmother.name
    father.father = child.name  # Cycle introduced here

    case = create_case([child, father, mother, grandfather, grandmother])
    return create_tomte_order([case])


@pytest.fixture
def order_with_existing_sample_cycle():
    child: TomteSample = create_tomte_sample(1)
    father = ExistingSample(internal_id="ExistingSampleInternalId", status=StatusEnum.unaffected)
    mother: TomteSample = create_tomte_sample(3)
    grandfather: TomteSample = create_tomte_sample(4)
    grandmother: TomteSample = create_tomte_sample(5)

    child.mother = mother.name
    child.father = "ExistingSampleName"

    father.mother = grandmother.name
    father.father = child.name  # Cycle introduced here

    case = create_case([child, father, mother, grandfather, grandmother])
    return create_tomte_order([case])


@pytest.fixture
def order_with_siblings_as_parents():
    child: TomteSample = create_tomte_sample(1)

    father: TomteSample = create_tomte_sample(3)
    mother: TomteSample = create_tomte_sample(4)

    grandfather: TomteSample = create_tomte_sample(5)
    grandmother: TomteSample = create_tomte_sample(6)

    child.father = father.name
    child.mother = mother.name

    father.mother = grandmother.name
    father.father = grandfather.name

    mother.mother = grandmother.name
    mother.father = grandfather.name

    case = create_case([child, father, mother, grandfather, grandmother])
    return create_tomte_order([case])


@pytest.fixture
def sample_with_invalid_concentration():
    sample: TomteSample = create_tomte_sample(1)
    sample.concentration_ng_ul = 1
    return sample


@pytest.fixture
def sample_with_missing_well_position():
    sample: TomteSample = create_tomte_sample(1)
    sample.well_position = None
    return sample


@pytest.fixture
def application_with_concentration_interval(base_store: Store) -> Application:
    application: Application = base_store.add_application(
        tag="RNAPOAR100",
        prep_category="wts",
        description="This is an application with concentration interval",
        percent_kth=100,
        percent_reads_guaranteed=90,
        sample_concentration_minimum=50,
        sample_concentration_maximum=250,
    )
    application.order_types = [OrderType.TOMTE]
    base_store.session.add(application)
    base_store.commit_to_store()
    return application


@pytest.fixture
def order_with_invalid_concentration(sample_with_invalid_concentration) -> TomteOrder:
    case: TomteCase = create_case([sample_with_invalid_concentration])
    order: TomteOrder = create_tomte_order([case])
    order.skip_reception_control = True
    return order


@pytest.fixture
def order_with_samples_having_same_names_as_cases() -> TomteOrder:
    """Return an order with two cases, the first case having two samples named after the cases."""
    sample_1: TomteSample = create_tomte_sample(1)
    sample_2: TomteSample = create_tomte_sample(2)
    sample_3: TomteSample = create_tomte_sample(3)
    case_1: TomteCase = create_case([sample_1, sample_2])
    case_1.name = sample_1.name
    case_2: TomteCase = create_case([sample_3])
    case_2.name = sample_2.name
    return create_tomte_order([case_1, case_2])


@pytest.fixture
def sample_with_missing_container_name() -> TomteSample:
    sample: TomteSample = create_tomte_sample(1)
    sample.container_name = None
    return sample


@pytest.fixture
def tomte_validation_service(
    base_store: Store,
    application_with_concentration_interval: Application,
) -> OrderValidationService:
    customer: Customer = base_store.get_customer_by_internal_id("cust000")
    user: User = base_store.add_user(customer=customer, email="mail@email.com", name="new user")
    base_store.session.add(user)
    base_store.session.add(application_with_concentration_interval)
    base_store.session.commit()
    return OrderValidationService(base_store)


@pytest.fixture
def application_tgs(base_store: Store) -> Application:
    application: Application = base_store.add_application(
        tag="PANKTTR020",
        prep_category=SeqLibraryPrepCategory.TARGETED_GENOME_SEQUENCING,
        description="Panel-based sequencing, 20 M read pairs.",
        percent_kth=59,
        percent_reads_guaranteed=75,
    )
    base_store.session.add(application)
    base_store.commit_to_store()
    return application


@pytest.fixture
def tomte_rule_set() -> RuleSet:
    return ORDER_TYPE_RULE_SET_MAP[OrderType.TOMTE]
