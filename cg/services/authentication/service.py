import time
from cg.services.user.service import UserService
from keycloak import KeycloakAuthenticationError, KeycloakOpenID
from keycloak.exceptions import KeycloakAuthenticationError, KeycloakGetError
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
        """Verify the token and return the user.

        Args:
            token (str): The token to verify.

        Returns:
            User: The user object from the statusDB database.

        Raises:
            ValueError: If the token is not active.
        """
        try:
            decoded_token: dict = self.client.decode_token(jwt_token)
            user_email = decoded_token["email"]
            return self.user_service.get_user_by_email(user_email)
        except KeycloakAuthenticationError as e:
            LOG.error(f"Token verification failed: {e}")
            raise

    def get_user_info(self, token: dict) -> dict:
        """Get the user information.
        Args:
            token (dict): The token dictionary containing the access token.

        Returns:
            dict: The user information.
        """
        try:
            return self.client.userinfo(token["access_token"])
        except KeycloakGetError as e:
            LOG.error(f"Failed to get user info: {e}")
            raise

    def get_token(self, code: str) -> dict:
        """Get the user token.
        Args:
            code (str): The authorization code.
        Returns:
            dict: The token dictionary.
        """
        try:
            return self.client.token(
                grant_type="authorization_code", code=code, redirect_uri=self.redirect_uri
            )
        except KeycloakAuthenticationError as e:
            LOG.error(f"Failed to get token: {e}")
            raise

    def check_user_role(self, access_token: str) -> bool:
        """Check if the user has the required role.

        Args:
            token (str): The access token for a user token.
            required_role (str): The role to check.

        Returns:
            None

        Raises:
            KeycloakAuthenticationError: If the user does not have the required role.
        """
        token_introspect: dict = self.client.introspect(access_token)
        roles = token_introspect.get("realm_access", {}).get("roles", [])
        if not "cg-employee" in roles:
            return False
        return True


    def refresh_access_token(self, refresh_token: str) -> dict:
        """
        Refresh the user tokens.
        Args:
            refresh_token: the refresh token of the user
        Raises:
            KeycloakAuthenticationError: if the token refresh failed.
        """
        try:
            return self.client.refresh_token(refresh_token)
        except KeycloakAuthenticationError as error:
            LOG.error(f"Token refresh failed {error}")
            raise
        
    def refresh_token(self, token: str) -> dict:
        """
        Refresh the token when it is about to expire.
        
        Args: 
            token_info: dict, the token information retrieved from the token introspection.
        """
        decoded_token: dict = self.decode_access_token
        expiration_time: int = token_info.get("exp")
        LOG.debug(f"#############Token expires at {expiration_time}###########")
        expires_in_less_than_a_minute: bool = expiration_time < time.time() +60      
        if expiration_time and expires_in_less_than_a_minute:
            LOG.debug("###########User token expired, getting a new token.#############")
            refresh_token = token_info.get("refresh_token")
            if not refresh_token:
                raise KeycloakAuthenticationError(error_message="Could not find refresh token")
            new_tokens: dict = self.refresh_access_token(refresh_token)
            return new_tokens