from unittest.mock import MagicMock, patch
from keycloak import KeycloakConnectionError
import pytest

from cg.clients.authentication.keycloak_client import KeycloakClient

# Assuming KeycloakOpenID and KeycloakConnectionError are imported or defined elsewhere

def test_get_client_success(mocker):
    # Mock the KeycloakOpenID class
    mock_keycloak_openid = mocker.patch("cg.clients.authentication.keycloak_client.KeycloakOpenID")
    mock_instance = MagicMock()
    mock_keycloak_openid.return_value = mock_instance

    # WHEN instantiating a keycloak client
    client = KeycloakClient(
        server_url="server_url",
        client_id="client_id",
        realm_name="name",
        client_secret_key="key",
        redirect_uri="uri"
    )

    # THEN get_client should return the mocked instance
    returned_client = client.get_client()
    assert returned_client == mock_instance

    # THEN KeycloakOpenID was called with the correct parameters
    mock_keycloak_openid.assert_called_once_with(
        server_url="server_url",
        client_id="client_id",
        realm_name="name",
        client_secret_key="key",
    )

    # Call get_client again to ensure the same instance is returned
    same_client = client.get_client()
    assert same_client == returned_client

def test_get_client_connection_error(mocker):
    # GIVEN a KeycloakOpenID class that raises KeycloakConnectionError
    mocker.patch("cg.clients.authentication.keycloak_client.KeycloakOpenID", side_effect=KeycloakConnectionError("Connection failed"))

    # WHEN instantiating a keycloak client with wrong information
    client = KeycloakClient(
        server_url="wrong_server_url",
        client_id="client_id",
        realm_name="name",
        client_secret_key="key",
        redirect_uri="uri"
    )

    # THEN get_client should raise a KeycloakConnectionError
    with pytest.raises(KeycloakConnectionError, match="Failed to connect to Keycloak: Connection failed"):
        client.get_client()

def test_get_client_general_exception(mocker):
    # GIVEN a KeycloakOpenID class that raises an Exception
    mocker.patch("cg.clients.authentication.keycloak_client.KeycloakOpenID", side_effect=Exception("General error"))

    # WHEN instantiating a keycloak client
    client = KeycloakClient(
        server_url="server_url",
        client_id="client_id",
        realm_name="name",
        client_secret_key="key",
        redirect_uri="uri"
    )

    # THEN get_client should raise a general exception
    with pytest.raises(Exception, match="An error occurred while creating Keycloak client: General error"):
        client.get_client()
