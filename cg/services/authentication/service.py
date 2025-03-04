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

        Raises:
            ValueError: If the token is not active.
        """
        try:
            decoded_token: dict = self.client.decode_token(jwt_token)
            LOG.info(f"Decoded token: {decoded_token}")
            if not self.has_required_role(decoded_token.get("realm_access", {})):
                raise ValueError("User not permitted, role requirement not met.")
            user_email = decoded_token["email"]
            return self.user_service.get_user_by_email(user_email)
        except KeycloakAuthenticationError as e:
            LOG.error(f"Token verification failed: {e}")
            raise

    @staticmethod
    def has_required_role(realm_access: dict) -> bool:
        roles = realm_access.get("roles", [])
        if not "cg-employee" in roles:
            return False
        return True

    def check_user_role(self, access_token: str) -> bool:
        """Check if the user has the required role using the access token.
        Args:
            token (str): The access token for a user token.
            required_role (str): The role to check.
        Returns:
            bool
        Raises:
            KeycloakAuthenticationError: If the user does not have the required role.
        """
        token_introspect: dict = self.client.introspect(access_token)
        LOG.info(f"{token_introspect}")
        access = token_introspect.get("realm_access", {})
        if not access:
            return False
        return self.has_required_role(access)

    def refresh_token(self, token: dict) -> dict:
        """
        Refresh a token if it expires in less than 10 minutes.
        Args:
            token: the token dictionary from keycloak
        """
        expires_in: int = int(token.get("expires_in"))
        if expires_in < 600:  # Expires in ten minutes
            return self.client.refresh_token(token.get("refresh_token"))
        return token
