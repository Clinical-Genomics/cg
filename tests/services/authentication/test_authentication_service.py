import pytest
from unittest.mock import MagicMock
from cg.services.authentication.exc import UserNotFoundError, UserRoleError
from cg.services.authentication.service import AuthenticationService
from cg.services.user.service import UserService
from keycloak import KeycloakOpenID
from cg.store.models import User


def test_verify_token_success(decode_token_response):
    
    # GIVEN a mock user service and a keycloak client
    mock_user_service = MagicMock(spec=UserService)
    mock_keycloak_client = MagicMock(spec=KeycloakOpenID)

    # GIVEN mocked responses from the services
    mock_keycloak_client.decode_token.return_value = decode_token_response.dict()
    mock_user_service.get_user_by_email.return_value = User(email=decode_token_response.email)

    # GIVEN an AuthenticationService
    auth_service = AuthenticationService(
        user_service=mock_user_service,
        redirect_uri="redirect_uri",
        keycloak_client=mock_keycloak_client
    )

    # WHEN verifying a jwt token
    user: User = auth_service.verify_token("jwt_token")

    # THEN the token is verified and a user with the email is returned
    assert user.email == decode_token_response.email
    mock_keycloak_client.decode_token.assert_called_once_with("jwt_token")
    mock_user_service.get_user_by_email.assert_called_once_with(decode_token_response.email)

def test_verify_token_user_not_found(decode_token_response):
     # GIVEN a mock user service and a keycloak client
    mock_user_service = MagicMock(spec=UserService)
    mock_keycloak_client = MagicMock(spec=KeycloakOpenID)

    # GIVEN that a user cannot be found with
    mock_keycloak_client.decode_token.return_value = decode_token_response.dict()
    mock_user_service.get_user_by_email.side_effect = ValueError("User not found")

    # GIVEN an AuthenticationService
    auth_service = AuthenticationService(
        user_service=mock_user_service,
        redirect_uri="redirect_uri",
        keycloak_client=mock_keycloak_client
    )

    # WHEN verifying the jwt token
    
    # THEN an UserNotFoundError is raised
    with pytest.raises(UserNotFoundError):
        auth_service.verify_token("jwt_token")

def test_verify_token_invalid_role(decode_token_response):
    # GIVEN a mock user service and a keycloak client
    mock_user_service = MagicMock(spec=UserService)
    mock_keycloak_client = MagicMock(spec=KeycloakOpenID)
    
     # GIVEN a decoded token response with an invalid user role
    decode_token_response.realm_access.roles = ["invalid-role"]
    mock_keycloak_client.decode_token.return_value = decode_token_response.dict()

    # GIVEN an AuthenticationService
    auth_service = AuthenticationService(
        user_service=mock_user_service,
        redirect_uri="redirect_uri",
        keycloak_client=mock_keycloak_client
    )

    # WHEN verifying the jwt token
    
    # THEN an UserRoleError is raised
    with pytest.raises(UserRoleError, match="The user does not have the required role to access this service."):
        auth_service.verify_token("jwt_token")

def test_get_user_roles_success(introspection_response):
    # GIVEN a mock user service and a keycloak client
    mock_user_service = MagicMock(spec=UserService)
    mock_keycloak_client = MagicMock(spec=KeycloakOpenID)

    # GIVEN an introspection response
    mock_keycloak_client.introspect.return_value = introspection_response.dict()

    # GIVEN an AuthenticationService
    auth_service = AuthenticationService(
        user_service=mock_user_service,
        redirect_uri="redirect_uri",
        keycloak_client=mock_keycloak_client
    )

    # WHEN retrieving the user roles
    roles = auth_service.get_user_roles("access_token")

    # THEN the right roles are returned
    assert roles == introspection_response.realm_access.roles
    
    # THEN the introspection endpoint is called
    mock_keycloak_client.introspect.assert_called_once_with("access_token")