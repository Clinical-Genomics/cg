import os
from pathlib import Path
from unittest.mock import Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

import cg.cli.events as events_cli
from cg.cli.events import listen
from cg.models.cg_config import CGConfig, NatsAuthentication, NatsConfig
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture(autouse=True)
def mock_path_read_text(mocker: MockerFixture):
    mocker.patch.object(Path, "read_text", return_value="my-token")


@pytest.fixture
def nats_config() -> NatsConfig:
    auth = NatsAuthentication(
        ca_cert_path=Path("ca/cert/path"),
        client_cert_path=Path("client/cert/path"),
        client_key_path=Path("client/key/path"),
        token_path=Path("token/path"),
    )
    return NatsConfig(
        server="nats://server",
        stream="cg-test",
        nats_binary_path=Path("nats/binary/path"),
        listener=auth,
        publisher=auth,
    )


@pytest.fixture
def config(nats_config: NatsConfig) -> CGConfig:
    return create_autospec(CGConfig, nats=nats_config)


@pytest.fixture(autouse=True)
def event_listener(mocker: MockerFixture) -> TypedMock[EventListener]:
    listener: TypedMock[EventListener] = create_typed_mock(EventListener)
    mocker.patch.object(events_cli, "EventListener", return_value=listener.as_type)
    return listener


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_store_and_db(mocker: MockerFixture):
    mocker.patch.object(events_cli, "Store")
    mocker.patch.dict(os.environ, {"CG_SQL_DATABASE_URI": "sqlite:///test.db"})


def test_listen(
    mocker: MockerFixture,
    cli_runner: CliRunner,
    config: CGConfig,
    event_listener: TypedMock[EventListener],
):
    # GIVEN a configured listener, store, and database URI in the environment
    initialize_database: Mock = mocker.patch.object(events_cli, "initialize_database")
    handler: Mock = Mock()
    mocker.patch.object(upload_handler, "completed", return_value=handler)

    # WHEN the listen command is invoked
    result: Result = cli_runner.invoke(listen, obj=config)

    # THEN the command exits without error
    assert result.exit_code == 0

    # THEN the database is initialized with the URI from the environment
    initialize_database.assert_called_once_with("sqlite:///test.db")

    # THEN the listener is registered with the upload.completed subject
    event_listener.as_mock.register.assert_called_once_with(
        "cg-test.analysis.upload_completed", handler
    )
