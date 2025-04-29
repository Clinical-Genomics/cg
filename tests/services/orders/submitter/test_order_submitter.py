import datetime as dt
from typing import Any, Generator
from unittest.mock import Mock, PropertyMock, create_autospec, patch

import pytest
from pytest_mock import mocker

from cg.clients.freshdesk.constants import Status
from cg.clients.freshdesk.models import TicketResponse
from cg.constants.constants import DataDelivery
from cg.exc import TicketCreationError
from cg.meta.orders.utils import get_ticket_status, get_ticket_tags
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import ContainerEnum, SexEnum
from cg.services.orders.constants import ORDER_TYPE_WORKFLOW_MAP
from cg.services.orders.storing.constants import MAF_ORDER_ID
from cg.services.orders.submitter.service import OrderSubmitter
from cg.services.orders.validation.errors.validation_errors import ValidationErrors
from cg.services.orders.validation.models.case import Case as ValidationCase
from cg.services.orders.validation.models.existing_case import ExistingCase
from cg.services.orders.validation.models.existing_sample import ExistingSample
from cg.services.orders.validation.models.order import Order
from cg.services.orders.validation.models.order_with_cases import OrderWithCases
from cg.services.orders.validation.models.order_with_samples import OrderWithSamples
from cg.services.orders.validation.models.sample import Sample as ValidationSample
from cg.services.orders.validation.order_types.balsamic.models.sample import BalsamicSample
from cg.services.orders.validation.order_types.mip_dna.models.order import MIPDNAOrder
from cg.store.models import Application, Case
from cg.store.models import Order as DbOrder
from cg.store.models import Pool, Sample, User
from cg.store.store import Store


def monkeypatch_process_lims(monkeypatch: pytest.MonkeyPatch, order: Order) -> None:
    lims_project_data = {"id": "ADM1234", "date": dt.datetime.now()}
    if isinstance(order, OrderWithSamples):
        lims_map = {sample.name: f"ELH123A{index}" for index, sample in enumerate(order.samples)}
    elif isinstance(order, OrderWithCases):
        lims_map = {
            sample.name: f"ELH123A{case_index}-{sample_index}"
            for case_index, sample_index, sample in order.enumerated_new_samples
        }
    monkeypatch.setattr(
        "cg.services.orders.lims_service.service.OrderLimsService.process_lims",
        lambda *args, **kwargs: (lims_project_data, lims_map),
    )


def mock_freshdesk_ticket_creation(mock_create_ticket: callable, ticket_id: str):
    """Helper function to mock Freshdesk ticket creation."""
    mock_create_ticket.return_value = TicketResponse(
        id=int(ticket_id),
        description="This is a test description.",
        subject="Support needed..",
        status=2,
        priority=1,
    )


def mock_freshdesk_reply_to_ticket(mock_reply_to_ticket: callable):
    """Helper function to mock Freshdesk reply to ticket."""
    mock_reply_to_ticket.return_value = None


@pytest.fixture
def external_app_name() -> str:
    return "external_app"


@pytest.fixture
def existing_case_id() -> str:
    return "existing_case_id"


@pytest.fixture
def existing_sample_id() -> str:
    return "existing_sample_id"


@pytest.fixture
def store_with_externals(
    external_app_name: str, existing_case_id: str, existing_sample_id: str
) -> Store:
    sample: Sample = create_autospec(Sample, instance=True)
    type(sample).is_external = PropertyMock(return_value=True)  # type: ignore

    store: Store = create_autospec(Store, instance=True)
    store.get_application_by_tag = lambda tag: (
        Application(is_external=True) if tag == external_app_name else None
    )

    store.get_samples_by_case_id = lambda case_id: ([sample] if case_id == existing_case_id else [])
    store.get_sample_by_internal_id = lambda internal_id: (
        sample if internal_id == existing_sample_id else None
    )

    return store


@pytest.fixture
def store_with_no_externals() -> Store:
    sample: Sample = create_autospec(Sample, instance=True)
    type(sample).is_external = PropertyMock(return_value=False)  # type: ignore

    store: Store = create_autospec(Store, instance=True)
    store.get_sample_by_internal_id.return_value = sample
    store.get_application_by_tag.return_value = Application(is_external=False)

    return store


@pytest.fixture
def order_with_one_external_sample(external_app_name: str) -> OrderWithSamples:
    return OrderWithSamples(
        customer="test_customer",
        delivery_type=DataDelivery.ANALYSIS_FILES,
        name="order with external data sample",
        project_type=OrderType.MICROSALT,
        samples=[
            ValidationSample(
                application="missing_app",
                container=ContainerEnum.no_container,
                name="ExternalSample",
            ),
            ValidationSample(
                application=external_app_name,
                container=ContainerEnum.no_container,
                name="ExternalSample",
            ),
        ],
    )


@pytest.fixture
def order_with_new_case_and_new_external_sample(external_app_name: str) -> OrderWithCases:
    return OrderWithCases(
        delivery_type=DataDelivery.ANALYSIS_SCOUT,
        cases=[
            ValidationCase(
                name="new-case",
                samples=[
                    BalsamicSample(
                        application=external_app_name,
                        container=ContainerEnum.no_container,
                        name="new-sample",
                        sex=SexEnum.female,
                        source="a source",
                        subject_id="subject-id",
                    ),
                ],
            ),
        ],
        customer="test_customer",
        project_type=OrderType.BALSAMIC,
        name="order with new cases and external sample data",
    )


@pytest.fixture
def order_with_new_case_and_existing_external_samples(existing_sample_id: str) -> OrderWithCases:
    return OrderWithCases(
        delivery_type=DataDelivery.ANALYSIS_SCOUT,
        cases=[
            ValidationCase(
                name="new-case",
                samples=[
                    ExistingSample(father="a", mother="b", internal_id=existing_sample_id),
                    ExistingSample(father="c", mother="d", internal_id="sample_not_in_database"),
                ],
            )
        ],
        customer="test_customer",
        project_type=OrderType.BALSAMIC,
        name="order with new case and existing external sample data",
    )


@pytest.fixture
def order_with_existing_case_and_external_sample(existing_case_id: str) -> OrderWithCases:
    return OrderWithCases(
        delivery_type=DataDelivery.ANALYSIS_FILES,
        cases=[ExistingCase(internal_id=existing_case_id)],
        customer="test_customer",
        project_type=OrderType.BALSAMIC_UMI,
        name="order with existing case and external sample data",
    )


@pytest.mark.parametrize(
    "order_type, order_fixture",
    [
        (OrderType.BALSAMIC, "balsamic_order"),
        (OrderType.FASTQ, "fastq_order"),
        (OrderType.FLUFFY, "fluffy_order"),
        (OrderType.METAGENOME, "metagenome_order"),
        (OrderType.MICROBIAL_FASTQ, "microbial_fastq_order"),
        (OrderType.MICROSALT, "microsalt_order"),
        (OrderType.MIP_DNA, "mip_dna_order"),
        (OrderType.MIP_RNA, "mip_rna_order"),
        (OrderType.NALLO, "nallo_order"),
        (OrderType.PACBIO_LONG_READ, "pacbio_order"),
        (OrderType.RML, "rml_order"),
        (OrderType.RNAFUSION, "rnafusion_order"),
        (OrderType.SARS_COV_2, "mutant_order"),
        (OrderType.TAXPROFILER, "taxprofiler_order"),
        (OrderType.TOMTE, "tomte_order"),
    ],
)
def test_submit_order(
    store_to_submit_and_validate_orders: Store,
    monkeypatch: pytest.MonkeyPatch,
    order_type: OrderType,
    order_fixture: str,
    order_submitter: OrderSubmitter,
    ticket_id: str,
    customer_id: str,
    request: pytest.FixtureRequest,
):
    """Test submitting a valid order of each ordertype."""
    # GIVEN an order
    order: Order = request.getfixturevalue(order_fixture)

    # GIVEN a store without samples, cases, or pools
    assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()
    assert not store_to_submit_and_validate_orders._get_query(table=Case).first()
    assert not store_to_submit_and_validate_orders._get_query(table=Pool).first()

    # GIVEN that the only order in store is a MAF order
    orders: list[DbOrder] = store_to_submit_and_validate_orders._get_query(table=DbOrder).all()
    assert len(orders) == 1
    assert orders[0].id == MAF_ORDER_ID

    # GIVEN a ticketing system that returns a ticket number
    with (
        patch(
            "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket"
        ) as mock_create_ticket,
        patch(
            "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.reply_to_ticket"
        ) as mock_reply_to_ticket,
    ):
        mock_freshdesk_ticket_creation(mock_create_ticket=mock_create_ticket, ticket_id=ticket_id)
        mock_freshdesk_reply_to_ticket(mock_reply_to_ticket)

        # GIVEN a mock LIMS that returns project data and sample name mapping
        monkeypatch_process_lims(monkeypatch=monkeypatch, order=order)

        # GIVEN a registered user
        user: User = store_to_submit_and_validate_orders._get_query(table=User).first()

        # GIVEN the dict representation of the order and a store without samples
        raw_order = order.model_dump(by_alias=True)
        assert not store_to_submit_and_validate_orders._get_query(table=Sample).first()

        # WHEN submitting the order
        result = order_submitter.submit(order_type=order_type, raw_order=raw_order, user=user)

        # THEN the result should contain the project data
        assert result["project"]["id"] == "ADM1234"

        # THEN the records should contain the appropriate ticket id, customer id and data analysis
        is_pool_order: bool = False
        for record in result["records"]:
            assert record.customer.internal_id == customer_id
            if isinstance(record, Pool):
                assert record.ticket == ticket_id
                is_pool_order = True
            elif isinstance(record, Sample):
                assert record.original_ticket == ticket_id
            elif isinstance(record, Case):
                assert record.data_analysis == ORDER_TYPE_WORKFLOW_MAP[order_type]
                for link_obj in record.links:
                    assert link_obj.sample.original_ticket == ticket_id

        # THEN the order should be stored in the database
        assert store_to_submit_and_validate_orders.get_order_by_ticket_id(ticket_id=int(ticket_id))

        # THEN the samples should be stored in the database
        assert store_to_submit_and_validate_orders._get_query(table=Sample).first()

        # THEN the cases should be stored in the database
        assert store_to_submit_and_validate_orders._get_query(table=Case).first()

        # THEN the pools should be stored in the database if applicable
        if is_pool_order:
            assert store_to_submit_and_validate_orders._get_query(table=Pool).first()


def test_submit_ticketexception(
    order_submitter: OrderSubmitter,
    mip_dna_order: MIPDNAOrder,
):

    # GIVEN an order
    raw_order = mip_dna_order.model_dump()
    raw_order["project_type"] = mip_dna_order.order_type

    # GIVEN a registered user
    user: User = order_submitter.validation_service.store._get_query(table=User).first()

    # GIVEN a mock Freshdesk ticket creation that raises TicketCreationError
    with (
        patch(
            "cg.clients.freshdesk.freshdesk_client.FreshdeskClient.create_ticket",
            side_effect=TicketCreationError("ERROR"),
        ),
        patch(
            "cg.services.orders.validation.service.OrderValidationService._get_rule_validation_errors",
            return_value=ValidationErrors(),
        ),
    ):

        # WHEN the order is submitted and a TicketCreationError raised
        # THEN the TicketCreationError is not excepted
        with pytest.raises(TicketCreationError):
            order_submitter.submit(
                raw_order=raw_order, user=user, order_type=mip_dna_order.order_type
            )


@pytest.mark.parametrize(
    "order_fixture, order_type, expected_tags",
    [
        ("mip_dna_order_with_existing_samples", OrderType.MIP_DNA, ["mip-dna", "existing-data"]),
        ("mip_dna_order", OrderType.MIP_DNA, ["mip-dna"]),
    ],
)
def test_get_ticket_tags(
    request: pytest.FixtureRequest,
    order_fixture: str,
    order_type: OrderType,
    expected_tags: list[str],
    store_with_no_externals: Store,
):
    """Test that the correct tags are generated based on the order and order type."""

    # GIVEN an order with existing data and no external samples
    order: OrderWithCases = request.getfixturevalue(order_fixture)

    # WHEN getting the ticket tags
    tags: list[str] = get_ticket_tags(
        order=order, order_type=order_type, status_db=store_with_no_externals
    )

    # THEN the tags should be correct
    assert tags == expected_tags


def test_get_ticket_tags_with_external_data_sample_for_order_with_samples(
    order_with_one_external_sample: OrderWithSamples,
    store_with_externals: Store,
):

    # GIVEN an order with two samples, one including external data
    order: OrderWithSamples = order_with_one_external_sample

    # WHEN getting the ticket tags
    tags: list[str] = get_ticket_tags(
        order=order, order_type=order.order_type, status_db=store_with_externals
    )

    # THEN the tags should include external-data
    assert "external-data" in tags


def test_get_ticket_tags_with_external_data_for_order_with_new_case_and_existing_samples(
    order_with_new_case_and_existing_external_samples: OrderWithCases,
    store_with_externals: Store,
):

    # GIVEN an order with a new case and a new sample with external data
    order: OrderWithCases = order_with_new_case_and_existing_external_samples

    # WHEN getting the ticket tags
    tags: list[str] = get_ticket_tags(
        order=order, order_type=order.order_type, status_db=store_with_externals
    )

    # THEN the tags should include external data
    assert "external-data" in tags


def test_get_ticket_tags_with_external_data_for_order_with_new_case_and_new_samples(
    order_with_new_case_and_new_external_sample: OrderWithCases,
    store_with_externals: Store,
):

    # GIVEN an order with a new case and a new sample with external data
    order: OrderWithCases = order_with_new_case_and_new_external_sample

    # WHEN getting the ticket tags
    tags: list[str] = get_ticket_tags(
        order=order, order_type=order.order_type, status_db=store_with_externals
    )

    # THEN the tags should include external data
    assert "external-data" in tags


def test_get_ticket_tags_with_external_data_for_order_with_existing_case(
    order_with_existing_case_and_external_sample: OrderWithCases, store_with_externals: Store
):

    # GIVEN an existing case with an existing sample with external data
    order: OrderWithCases = order_with_existing_case_and_external_sample

    # WHEN getting the ticket tags
    tags: list[str] = get_ticket_tags(
        order=order, order_type=order.order_type, status_db=store_with_externals
    )

    # THEN the tags should include external data
    assert "external-data" in tags


@pytest.mark.parametrize(
    "order_fixture, expected_status",
    [
        ("mip_dna_order", Status.PENDING),
        ("mip_dna_order_with_existing_samples", Status.PENDING),
        ("mip_dna_order_with_only_existing_samples", Status.OPEN),
    ],
)
def test_get_ticket_status(
    request: pytest.FixtureRequest, order_fixture: str, expected_status: int
):
    """Test that the correct ticket status is returned based on the order samples."""

    # GIVEN an order
    order: Order = request.getfixturevalue(order_fixture)

    # WHEN getting the ticket status
    status = get_ticket_status(order=order)

    # THEN the status should be correct
    assert status == expected_status
