import pytest

from cg.services.delivery_message.delivery_message_service import DeliveryMessageService


def test_get_delivery_message(
    delivery_message_service: DeliveryMessageService,
    expected_message_fixture: str,
    case_ids_fixture: str,
    request: pytest.FixtureRequest,
) -> None:
    """Test that the delivery message is created correctly."""
    # GIVEN a delivery message service and a list of case IDs
    case_ids: set[str] = request.getfixturevalue(case_ids_fixture)

    # WHEN the delivery message is requested
    message: str = delivery_message_service._get_delivery_message(case_ids=case_ids)

    # THEN the message should be as expected
    expected_message: str = request.getfixturevalue(expected_message_fixture)
    assert message == expected_message
