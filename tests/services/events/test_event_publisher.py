import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import nats
from nats.aio.client import Client
from nats.js import JetStreamContext as JSC

from cg.models.cg_config import NatsConfig
from cg.services.events import event_publisher
from tests.typed_mock import TypedMock, create_typed_mock


def test_publish_command():
    # GIVEN a NatsConfig with publisher authentication details, a subject, and data
    nats_config = NatsConfig(
        server="nats://server",
        stream="cg-test",
        nats_binary_path=Path("nats_binary"),
        ca_cert_path=Path("ca_cert"),
        client_cert_path=Path("client_cert"),
        client_key_path=Path("client_key"),
        token_path=Path("/token/path"),
    )
    subject = "cg.upload.completed"
    data = {"analysis": "analysis_1", "uploaded_at": "$(date +%Y-%m-%dT%H:%M:%SZ)"}

    # WHEN the publish_command function is called with the NatsConfig, subject, and data
    command = event_publisher.publish_command(nats_config=nats_config, subject=subject, data=data)

    # THEN the generated command string matches the expected format
    expected = (
        "nats_binary pub "
        "--jetstream "
        "--server nats://server "
        "--tlsca ca_cert "
        "--tlscert client_cert "
        "--tlskey client_key "
        "--token $(cat /token/path) "
        r'cg.upload.completed "{\"analysis\": \"analysis_1\", \"uploaded_at\": \"$(date +%Y-%m-%dT%H:%M:%SZ)\"}"'
    )
    assert command == expected


def test_publish(mocker):
    # GIVEN a NatsConfig, a subject and payload
    nats_config = NatsConfig(
        server="nats://server",
        stream="cg-test",
        nats_binary_path=Path("nats_binary"),
        ca_cert_path=Path("ca_cert"),
        client_cert_path=Path("client_cert"),
        client_key_path=Path("client_key"),
        token_path=Path("/token/path"),
    )
    subject = "cg.upload.completed"
    data = {"analysis": "analysis_1"}

    # GIVEN a mocked nats client and jetstream context
    jetstream_context: TypedMock[JSC] = create_typed_mock(JSC)
    jetstream_context.as_mock.publish = AsyncMock()

    nats_client: TypedMock[Client] = create_typed_mock(Client)
    nats_client.as_mock.jetstream.return_value = jetstream_context.as_type
    nats_client.as_mock.drain = AsyncMock()

    connect_mock = mocker.patch.object(nats, "connect", AsyncMock(return_value=nats_client.as_type))
    mocker.patch.object(event_publisher.Path, "read_text", return_value="nats-token")
    tls_context = Mock()
    mocker.patch.object(event_publisher, "_tls_context", return_value=tls_context)

    # WHEN publishing synchronously
    event_publisher.publish(nats_config=nats_config, subject=subject, event_payload=data)

    # THEN the event is sent via JetStream
    connect_mock.assert_awaited_once_with(
        servers="nats://server", tls=tls_context, token="nats-token"
    )
    jetstream_context.as_mock.publish.assert_awaited_once_with(
        subject=subject,
        payload=json.dumps(data).encode(),
    )
    nats_client.as_mock.drain.assert_awaited_once()


def test_publish_async(mocker):
    # GIVEN a NatsConfig, a subject and payload
    nats_config = NatsConfig(
        server="nats://server",
        stream="cg-test",
        nats_binary_path=Path("nats_binary"),
        ca_cert_path=Path("ca_cert"),
        client_cert_path=Path("client_cert"),
        client_key_path=Path("client_key"),
        token_path=Path("/token/path"),
    )
    subject = "cg.upload.completed"
    data = {"analysis": "analysis_1"}

    # GIVEN a mocked nats client and jetstream context
    jetstream_context: TypedMock[JSC] = create_typed_mock(JSC)
    jetstream_context.as_mock.publish = AsyncMock()

    nats_client: TypedMock[Client] = create_typed_mock(Client)
    nats_client.as_mock.jetstream.return_value = jetstream_context.as_type
    nats_client.as_mock.drain = AsyncMock()

    connect_mock = mocker.patch.object(nats, "connect", AsyncMock(return_value=nats_client.as_type))
    mocker.patch.object(event_publisher.Path, "read_text", return_value="nats-token")
    tls_context = Mock()
    mocker.patch.object(event_publisher, "_tls_context", return_value=tls_context)

    # WHEN publishing asynchronously
    asyncio.run(event_publisher.publish_async(nats_config=nats_config, subject=subject, data=data))

    # THEN the event is sent via JetStream
    connect_mock.assert_awaited_once_with(
        servers="nats://server", tls=tls_context, token="nats-token"
    )
    jetstream_context.as_mock.publish.assert_awaited_once_with(
        subject=subject,
        payload=json.dumps(data).encode(),
    )
    nats_client.as_mock.drain.assert_awaited_once()
