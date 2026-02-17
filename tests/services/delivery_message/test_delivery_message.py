from string import Template

import pytest

from cg.constants.constants import DataDelivery, Workflow
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.store.models import Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize(
    "case_id_fixture, expected_message_fixture",
    [
        ("fluffy_case_id", "statina_message"),
        ("microsalt_case_id", "microsalt_message"),
        ("mip_case_id", "analysis_scout_message"),
    ],
    ids=[
        "STATINA",
        "microSALT",
        "ANALYSIS_SCOUT",
    ],
)
def test_get_delivery_message_for_single_case(
    delivery_message_service: DeliveryMessageService,
    case_id_fixture: str,
    expected_message_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the delivery message is created correctly for a given case."""
    # GIVEN a delivery message service and a list of case IDs
    case_ids: str = request.getfixturevalue(case_id_fixture)

    # WHEN the delivery message is requested
    message: str = delivery_message_service._get_delivery_message(case_ids={case_ids})

    # THEN the message should be as expected
    expected_message: str = request.getfixturevalue(expected_message_fixture)
    assert message == expected_message


@pytest.mark.parametrize(
    "workflow, delivery_type, expected_message_template_fixture",
    [
        (
            Workflow.NALLO,
            DataDelivery.RAW_DATA_ANALYSIS,
            "raw_data_analysis_message",
        ),
        (
            Workflow.NALLO,
            DataDelivery.RAW_DATA_ANALYSIS_SCOUT,
            "raw_data_analysis_scout38_message",
        ),
        (
            Workflow.NALLO,
            DataDelivery.RAW_DATA_SCOUT,
            "raw_data_scout38_message",
        ),
        (
            Workflow.RAREDISEASE,
            DataDelivery.RAW_DATA_ANALYSIS,
            "raw_data_analysis_message",
        ),
        (
            Workflow.RAREDISEASE,
            DataDelivery.RAW_DATA_ANALYSIS_SCOUT,
            "raw_data_analysis_scout38_message",
        ),
        (
            Workflow.RAREDISEASE,
            DataDelivery.RAW_DATA_SCOUT,
            "raw_data_scout38_message",
        ),
    ],
    ids=[
        "NALLO_RAW_DATA_ANALYSIS",
        "NALLO_RAW_DATA_ANALYSIS_SCOUT",
        "NALLO_RAW_DATA_SCOUT",
        "RAREDISEASE_RAW_DATA_ANALYSIS",
        "RAREDISEASE_RAW_DATA_ANALYSIS_SCOUT",
        "RAREDISEASE_RAW_DATA_SCOUT",
    ],
)
def test_get_delivery_message_scout38_case(
    delivery_message_service: DeliveryMessageService,
    helpers: StoreHelpers,
    workflow: Workflow,
    delivery_type: DataDelivery,
    expected_message_template_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the delivery message is created correctly for a given case."""
    # GIVEN a delivery message service and case ID

    # GIVEN that the store contains the case
    store: Store = delivery_message_service.store
    order: Order = store.get_order_by_id(1)
    helpers.ensure_case(
        store=store,
        case_id="case_id",
        case_name="case_id",
        data_analysis=workflow,
        data_delivery=delivery_type,
        order=order,
    )

    # WHEN the delivery message is requested
    message: str = delivery_message_service._get_delivery_message(case_ids={"case_id"})

    # THEN the message should be as expected
    expected_message_template: Template = request.getfixturevalue(expected_message_template_fixture)
    expected_message: str = expected_message_template.substitute(
        case_id="case_id", customer_id=order.customer.internal_id, ticket_id=order.ticket_id
    )

    assert message == expected_message
