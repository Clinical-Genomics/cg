from pathlib import Path

from cg.models.cg_config import NatsAuthentication, NatsConfig
from cg.services.events import event_publisher


def test_publish_command():
    # GIVEN a NatsConfig with publisher authentication details, a subject, and data
    nats_config = NatsConfig(
        server="nats://server",
        stream="cg-test",
        nats_binary_path=Path("nats_binary"),
        publisher=NatsAuthentication(
            ca_cert_path=Path("ca_cert"),
            client_cert_path=Path("client_cert"),
            client_key_path=Path("client_key"),
            token_path=Path("/token/path"),
        ),
        listener=NatsAuthentication(
            ca_cert_path=Path("ca_cert"),
            client_cert_path=Path("client_cert"),
            client_key_path=Path("client_key"),
            token_path=Path("token/path"),
        ),
    )
    subject = "cg.upload.completed"
    data = {"analysis": "analysis_1", "uploaded_at": "$(date +%Y-%m-%dT%H:%M:%SZ)"}

    # WHEN the publish_command function is called with the NatsConfig, subject, and data
    command = event_publisher.publish_command(nats_config=nats_config, subject=subject, data=data)

    # THEN the generated command string matches the expected format
    expected = (
        "nats_binary pub "
        "--server nats://server "
        "--tlsca ca_cert "
        "--tlscert client_cert "
        "--tlskey client_key "
        "--token $(cat /token/path) "
        r'cg.upload.completed "{\"analysis\": \"analysis_1\", \"uploaded_at\": \"$(date +%Y-%m-%dT%H:%M:%SZ)\"}"'
    )
    assert command == expected
