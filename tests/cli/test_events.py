from pathlib import Path
from unittest.mock import create_autospec

from click.testing import CliRunner

from cg.cli.events import listen
from cg.models.cg_config import CGConfig, NatsAuthentication, NatsConfig


def test_listen():
    # GIVEN a CGConfig with NATS configuration
    config = create_autospec(
        CGConfig,
        nats=NatsConfig(
            server="nats://server",
            stream="cg-test",
            nats_binary_path=Path("nats/binary/path"),
            listener=NatsAuthentication(
                ca_cert_path=Path("ca/cert/path"),
                client_cert_path=Path("client/cert/path"),
                client_key_path=Path("client/key/path"),
                token_path=Path("token/path"),
            ),
            publisher=NatsAuthentication(
                ca_cert_path=Path("ca/cert/path"),
                client_cert_path=Path("client/cert/path"),
                client_key_path=Path("client/key/path"),
                token_path=Path("token/path"),
            ),
        ),
    )

    # WHEN the listen command is invoked with the CGConfig
    cli_runner = CliRunner()
    cli_runner.invoke(listen, obj=config)

    # THEN the command exits without error
