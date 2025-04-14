import mock
import pytest

from cg.constants.constants import MicrosaltAppTags
from cg.services.delivery_message.delivery_message_service import DeliveryMessageService


@pytest.mark.parametrize(
    "case_id_fixture, expected_message_fixture, app_tag",
    [
        ("microsalt_mwr_case_id", "microsalt_mwr_message", MicrosaltAppTags.MWRNXTR003),
        ("microsalt_mwx_case_id", "microsalt_mwx_message", MicrosaltAppTags.MWXNXTR003),
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
