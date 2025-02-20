from cg.io.xml import LOG
from cg.services.user.service import UserService
from keycloak import KeycloakOpenID

from cg.store.models import User
import logging

LOG = logging.getLogger(__name__)


class AuthenticationService:
    """Authentication service user to verify tokens against keycloak and return user information."""

    def __init__(
        self,
        user_service: UserService,
        server_url: str,
        client_id: str,
        client_secret: str,
        realm_name: str,
        redirect_uri: str,
    ):
        """_summary_

        Args:
            store (Store): Connection to statusDB
            server_url (str): server url to the keycloak server or container
            realm_name (str): the keycloak realm to connect to (can be found in keycloak)
            client_id (str): the client id to use in keycloak realm (can be found in keycloak)
            client_secret (str): the client secret to use in keycloak realm (can be found in keycloak)
            redirect_uri (str): the redirect uri to use
        """
        self.user_service: UserService = user_service
        self.server_url: str = server_url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.realm_name: str = realm_name
        self.redirect_uri: str = redirect_uri
        self.client: KeycloakOpenID = self._get_client()

    def _get_client(self):
        """Set the KeycloakOpenID client."""

        keycloak_openid_client = KeycloakOpenID(
            server_url=self.server_url,
            client_id=self.client_id,
            realm_name=self.realm_name,
            client_secret_key=self.client_secret,
        )
        return keycloak_openid_client

    def verify_token(self, token: str) -> User:
        """Verify the token and return the user.
        args:
            token: str
        returns:
            User - the user object from the statusDB database NOTE: this is not the same as the user object in keycloak. This should be reworked in the future.
        raises:
            ValueError: if the token is not active
        """
        token_info = self.client.introspect(token)
        if not token_info["active"]:
            raise ValueError("Token is not active")
        verified_token = self.client.decode_token(token)
        user_email = verified_token["email"]
        return self.user_service.get_user_by_email(user_email)

    def get_auth_url(self):
        """Get the authentication url."""
        LOG.info(f"server_url: {self.server_url}")
        LOG.info(f"client_id: {self.client_id}")
        LOG.info(f"realm_name: {self.realm_name}")
        LOG.info(f"client_secret: {self.client_secret}")
        LOG.info(f"redirect_uri: {self.redirect_uri}")
        auth_url: str = self.client.auth_url(
            redirect_uri=self.redirect_uri, scope="openid profile email"
        )
        LOG.debug(f"auth url: {auth_url}")
        return auth_url

    def logout_user(self, refresh_token: str):
        """Logout the user
        args:
            refresh_token: str - the refresh token for the user in the current session. This is different from the normal token.
        """
        self.client.logout(refresh_token)

    def get_user_info(self, token):
        """
        Get the user information.
        """
        return self.client.userinfo(token["access_token"])

    def get_token(self, code: str):
        """
        Get the token the user token.
        """
        return self.client.token(
            grant_type="authorization_code", code=code, redirect_uri=self.redirect_uri
        )
