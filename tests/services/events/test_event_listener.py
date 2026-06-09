import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import nats
import pytest
from nats.aio.client import Client
from nats.aio.msg import Msg
from nats.js import JetStreamContext as JSC
from pytest_mock import MockerFixture

from cg.models.cg_config import NatsAuthentication, NatsConfig
from cg.services.events.event_listener import EventListener
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture(autouse=True)
def mock_path_read_text(mocker: MockerFixture):
    mocker.patch.object(Path, "read_text", return_value="my-token")


@pytest.fixture
def event_listener() -> EventListener:
    nats_authentication = NatsAuthentication(
        ca_cert_path=Path("/ca/cert/path"),
        client_cert_path=Path("/client/cert/path"),
        client_key_path=Path("/client/key/path"),
        token_path=Path("/token/path"),
    )
    return EventListener(
        config=NatsConfig(
            server="nats://server",
            nats_binary_path=Path("/nats/binary/path"),
            stream="stream-name",
            listener=nats_authentication,
            publisher=nats_authentication,
        )
    )


async def message_stream(*messages):
    for message in messages:
        yield message


def make_mock_message(subject: str, data: dict) -> TypedMock[Msg]:
    return create_typed_mock(Msg, subject=subject, data=json.dumps(data).encode())


def make_mock_nats(mocker: MockerFixture, subscription: TypedMock[JSC.PushSubscription]) -> None:
    jetstream_context: TypedMock[JSC] = create_typed_mock(JSC)
    jetstream_context.as_mock.subscribe.return_value = subscription.as_type

    nats_client: TypedMock[Client] = create_typed_mock(Client)
    nats_client.as_mock.jetstream.return_value = jetstream_context.as_type

    mocker.patch.object(nats, "connect", AsyncMock(return_value=nats_client.as_type))
    mocker.patch.object(EventListener, "_tls_context", return_value=Mock())


def test_listen_dispatches_to_registered_handler(
    mocker: MockerFixture, event_listener: EventListener
):
    # GIVEN a message on a subject with a registered handler
    payload: dict[str, str] = {"case_id": "abc123"}
    message: TypedMock[Msg] = make_mock_message("stream-name.my_subject", payload)

    subscription: TypedMock[JSC.PushSubscription] = create_typed_mock(JSC.PushSubscription)
    subscription.as_mock.messages = message_stream(message.as_type)
    make_mock_nats(mocker, subscription)

    handler: Mock = Mock()
    event_listener.register("stream-name.my_subject", handler)

    # WHEN listening for events
    asyncio.run(event_listener.listen())

    # THEN the handler is called with the parsed payload and the message is acked
    handler.assert_called_once_with(payload)
    message.as_mock.ack.assert_called_once()


def test_listen_acks_message_with_no_handler(mocker: MockerFixture, event_listener: EventListener):
    # GIVEN a message on a subject with no registered handler
    message: TypedMock[Msg] = make_mock_message("stream-name.unregistered_subject", {"x": 1})

    subscription: TypedMock[JSC.PushSubscription] = create_typed_mock(JSC.PushSubscription)
    subscription.as_mock.messages = message_stream(message.as_type)
    make_mock_nats(mocker, subscription)

    # WHEN listening for events
    asyncio.run(event_listener.listen())

    # THEN the message is still acked
    message.as_mock.ack.assert_called_once()
    message.as_mock.nak.assert_not_called()


def test_listen_naks_message_when_handler_raises(
    mocker: MockerFixture, event_listener: EventListener
):
    # GIVEN a message on a subject whose handler raises an exception
    message: TypedMock[Msg] = make_mock_message("stream-name.my_subject", {"x": 1})

    subscription: TypedMock[JSC.PushSubscription] = create_typed_mock(JSC.PushSubscription)
    subscription.as_mock.messages = message_stream(message.as_type)
    make_mock_nats(mocker, subscription)

    handler: Mock = Mock(side_effect=RuntimeError("boom"))
    event_listener.register("stream-name.my_subject", handler)

    # WHEN listening for events
    asyncio.run(event_listener.listen())

    # THEN the message is nacked instead of acked
    message.as_mock.nak.assert_called_once()
    message.as_mock.ack.assert_not_called()
