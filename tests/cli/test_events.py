from pathlib import Path
from unittest.mock import create_autospec

from click.testing import CliRunner
from pytest_mock import MockerFixture

from cg.cli.events import listen
from cg.models.cg_config import CGConfig, NatsAuthentication, NatsConfig


def test_listen(mocker: MockerFixture):
    config = create_autospec(
        CGConfig,
        nats=NatsConfig(
            server="nats://server",
            listener=NatsAuthentication(
                ca_cert_path=Path("ca/cert/path"),
                client_cert_path=Path("client/cert/path"),
                client_key_path=Path("client/key/path"),
                nats_binary_path=Path("nats/binary/path"),
                token_path=Path("token/path"),
            ),
            publisher=NatsAuthentication(
                ca_cert_path=Path("ca/cert/path"),
                client_cert_path=Path("client/cert/path"),
                client_key_path=Path("client/key/path"),
                nats_binary_path=Path("nats/binary/path"),
                token_path=Path("token/path"),
            ),
        ),
    )
    # TODO: Finish this test
    cli_runner = CliRunner()
    cli_runner.invoke(listen, obj=config)
