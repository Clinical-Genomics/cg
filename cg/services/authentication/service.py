from pydantic import ValidationError
from cg.services.authentication.exc import TokenIntrospectionError, UserNotFoundError, UserRoleError
from cg.services.authentication.models import (
    DecodingResponse,
    IntrospectionResponse,
    RealmAccess,
    TokenResponseModel,
)
from cg.services.user.service import UserService
from keycloak import KeycloakAuthenticationError, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError
from cg.store.models import User
import logging

LOG = logging.getLogger(__name__)


class AuthenticationService:
    """Authentication service to verify tokens against Keycloak and return user information."""

    def __init__(
        self,
        user_service: UserService,
        redirect_uri: str,
        keycloak_client: KeycloakOpenID,
    ):
        """Initialize the AuthenticationService.

        Args:
            user_service (UserService): Service to interact with user data.
            redirect_uri: Redirect uri for keycloak
            keycloak_client: KeycloakOpenID client.
        """
        self.user_service = user_service
        self.redirect_uri = redirect_uri
        self.client = keycloak_client

    def verify_token(self, jwt_token: str) -> User:
        """Verify the token and return the user if required roles are present.
        Args:
            token (str): The token to verify.

        Returns:
            User: The user object from the statusDB database.
        """
        try:
            decoded_token = DecodingResponse(**self.client.decode_token(jwt_token))
            self._check_role(decoded_token.realm_access)
            user_email = decoded_token.email
            return self.user_service.get_user_by_email(user_email)
        except ValueError as error:
            raise UserNotFoundError(f"{error}")

    @staticmethod
    def _check_role(realm_acces: RealmAccess) -> None:
        if not "cg-employee" in realm_acces.roles:
            raise UserRoleError(
                "Unauthorised, the user does not have the required role to access this service."
            )

    def check_user_role(self, access_token: str) -> None:
        """Check if the user has the required role using the access token.
        Args:
            token (str): The access token for a user token.
            required_role (str): The role to check.
        Returns:
            bool
        Raises:
            KeycloakAuthenticationError: If the user does not have the required role.
        """
        try:
            token_introspect = IntrospectionResponse(**self.client.introspect(access_token))
            self._check_role(token_introspect.realm_access)
        except ValidationError as error:
            raise TokenIntrospectionError(f"{error}")

    def refresh_token(self, token: TokenResponseModel) -> TokenResponseModel:
        """
        Refresh a token if it expires in less than 10 minutes. Otherwise return the current tokens.
        Args:
            token: TokenResponseModel
        """
        if token.expires_in < 600:  # Expires in ten minutes
            return TokenResponseModel(**self.client.refresh_token(token.refresh_token))
        return token
