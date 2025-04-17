import mock
import pytest

from cg.constants.constants import DataDelivery, MicrosaltAppTags, Workflow
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService
from cg.store.models import Order
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


@pytest.mark.parametrize(
    "case_id_fixture, expected_message_fixture, app_tag",
    [
        ("fluffy_case_id", "statina_message", None),
        ("microsalt_mwr_case_id", "microsalt_mwr_message", MicrosaltAppTags.MWRNXTR003),
        ("microsalt_mwx_case_id", "microsalt_mwx_message", MicrosaltAppTags.MWXNXTR003),
        ("mip_case_id", "analysis_scout_message", None),
    ],
    ids=[
        "STATINA",
        "microSALT_MWR",
        "microSALT_MWX",
        "ANALYSIS_SCOUT",
    ],
)
def test_get_delivery_message_for_single_case(
    delivery_message_service: DeliveryMessageService,
    case_id_fixture: str,
    expected_message_fixture: str,
    app_tag: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the delivery message is created correctly for a given case."""
    # GIVEN a delivery message service and a list of case IDs
    case_ids: str = request.getfixturevalue(case_id_fixture)

    # WHEN the delivery message is requested
    with mock.patch(
        "cg.services.delivery_message.utils.get_case_app_tag",
        return_value=app_tag,
    ):
        message: str = delivery_message_service._get_delivery_message(case_ids={case_ids})

    # THEN the message should be as expected
    expected_message: str = request.getfixturevalue(expected_message_fixture)
    assert message == expected_message


@pytest.mark.parametrize(
    "delivery_type, expected_message_fixture",
    [
        (DataDelivery.RAW_DATA_ANALYSIS, "nallo_raw_data_analysis_message"),
        (DataDelivery.RAW_DATA_ANALYSIS_SCOUT, "nallo_raw_data_analysis_scout_message"),
        (DataDelivery.RAW_DATA_SCOUT, "nallo_raw_data_scout_message"),
    ],
    ids=[
        "RAW_DATA_ANALYSIS",
        "RAW_DATA_ANALYSIS_SCOUT",
        "RAW_DATA_SCOUT",
    ],
)
def test_get_delivery_message_nallo_case(
    nallo_case_id: str,
    delivery_message_service: DeliveryMessageService,
    helpers: StoreHelpers,
    delivery_type: DataDelivery,
    expected_message_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the delivery message is created correctly for a given case."""
    # GIVEN a delivery message service and a Nallo case ID

    # GIVEN that the store contains the case
    store: Store = delivery_message_service.store
    order: Order = store.get_order_by_id(1)
    helpers.ensure_case(
        store=store,
        case_id=nallo_case_id,
        case_name=nallo_case_id,
        data_analysis=Workflow.NALLO,
        data_delivery=delivery_type,
        order=order,
    )

    # WHEN the delivery message is requested
    message: str = delivery_message_service._get_delivery_message(case_ids={nallo_case_id})

    # THEN the message should be as expected
    expected_message: str = request.getfixturevalue(expected_message_fixture)
    assert message == expected_message
