from cg.services.user.service import UserService
from keycloak import KeycloakOpenID

from cg.store.models import User


class AuthenticationService:
    """Authentication service user to verify tokens against keycloak and return user information."""

    def __init__(
        self, user_service: UserService, server_url: str, client_id: str, client_secret: str, realm_name: str
    ):
        """_summary_

        Args:
            store (Store): Connection to statusDB
            server_url (str): server url to the keycloak server or container
            realm_name (str): the keycloak realm to connect to (can be found in keycloak)
            client_id (str): the client id to use in keycloak realm (can be found in keycloak)
            client_secret (str): the client secret to use in keycloak realm (can be found in keycloak)  
        """
        self.user_service: UserService = user_service
        self.server_url: str = server_url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.realm_name: str = realm_name
        self.client: KeycloakOpenID = self._get_client()

    def _get_client(self):
        """Set the KeycloakOpenID client.
        """
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
            AuthenticatedUser
        raises:
            ValueError: if the token is not active
        """
        token_info = self.client.introspect(token)
        if not token_info['active']:
            raise ValueError('Token is not active')
        verified_token = self.client.decode_token(token)
        user_email = verified_token["email"]
        return self.user_service.get_user_by_email(user_email)
        

    
    