import os
from unittest.mock import Mock, create_autospec

import pytest
from click.testing import CliRunner, Result
from pytest_mock import MockerFixture

import cg.cli.listen as listen_cli
from cg.apps.tb.api import TrailblazerAPI
from cg.cli.listen import listen
from cg.services.events import upload_handler
from cg.services.events.event_listener import EventListener
from cg.store.store import Store
from tests.typed_mock import TypedMock, create_typed_mock


@pytest.fixture(autouse=True)
def event_listener(mocker: MockerFixture) -> TypedMock[EventListener]:
    listener: TypedMock[EventListener] = create_typed_mock(EventListener)
    mocker.patch.object(listen_cli, "EventListener", return_value=listener.as_type)
    return listener


@pytest.fixture
def cli_runner() -> CliRunner:
    return CliRunner()


@pytest.fixture(autouse=True)
def mock_store_and_db(mocker: MockerFixture):
    mocker.patch.object(listen_cli, "Store")
    mocker.patch.dict(os.environ, {"CG_SQL_DATABASE_URI": "sqlite:///test.db"})


@pytest.fixture(autouse=True)
def mock_trailblazer_config(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {"TRAILBLAZER_HOST": "https://tb.scilifelab.se"})
    mocker.patch.dict(os.environ, {"TRAILBLAZER_SERVICE_ACCOUNT": "tb-service-account"})
    mocker.patch.dict(os.environ, {"TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE": "auth.json"})


@pytest.fixture(autouse=True)
def mock_nats_config(mocker: MockerFixture):
    mocker.patch.dict(os.environ, {"NATS_STREAM": "nats-stream"})
    mocker.patch.dict(os.environ, {"NATS_SERVER": "nats://server"})
    mocker.patch.dict(os.environ, {"LISTENER_CA_CERT_PATH": "/path/to/listener_ca_cert"})
    mocker.patch.dict(os.environ, {"LISTENER_CLIENT_CERT_PATH": "/path/to/client_cert"})
    mocker.patch.dict(os.environ, {"LISTENER_CLIENT_KEY_PATH": "/path/to/client_key"})
    mocker.patch.dict(os.environ, {"LISTENER_TOKEN_PATH": "/path/to/token"})


def test_listen(
    mocker: MockerFixture,
    cli_runner: CliRunner,
    event_listener: TypedMock[EventListener],
):
    # GIVEN a configured listener, store, and database URI in the environment
    initialize_database: Mock = mocker.patch.object(listen_cli, "initialize_database")

    status_db = create_autospec(Store)
    mocker.patch.object(listen_cli, "Store", return_value=status_db)

    trailblazer_api = create_autospec(TrailblazerAPI)
    trailblazer_constructor = mocker.patch.object(
        listen_cli, "TrailblazerAPI", return_value=trailblazer_api
    )

    handler: Mock = Mock()
    handler_creator = mocker.patch.object(upload_handler, "completed", return_value=handler)

    # WHEN the listen command is invoked
    result: Result = cli_runner.invoke(listen, catch_exceptions=False)

    # THEN the command exits without error
    assert result.exit_code == 0

    # THEN the database is initialized with the URI from the environment
    initialize_database.assert_called_once_with("sqlite:///test.db")

    # THEN the trailblazer api is initialized with a config from the environment
    trailblazer_constructor.assert_called_once_with(
        config={
            "trailblazer": {
                "host": "https://tb.scilifelab.se",
                "service_account": "tb-service-account",
                "service_account_auth_file": "auth.json",
            }
        }
    )

    # THEN the handler was created with the correct dependencies
    handler_creator.assert_called_once_with(status_db=status_db, trailblazer_api=trailblazer_api)

    # THEN the listener is registered with the upload.completed subject
    event_listener.as_mock.register.assert_called_once_with(
        "nats-stream.analysis.upload_completed", handler
    )
