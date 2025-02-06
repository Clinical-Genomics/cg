from cycler import V
from cg.services.authentication.constants import ADMIN, CUSTOMER
from cg.store.models import User
from cg.store.store import Store
from keycloak import KeycloakError, KeycloakOpenID
from cg.services.authentication.models import AuthenticatedUser


class AuthenticationService:
    """Authentication service user to verify tokens against keycloak and return user information."""

    def __init__(
        self, store: Store, server_url: str, client_id: str, client_secret: str, realm_name: str
    ):
        """_summary_

        Args:
            store (Store): Connection to statusDB
            server_url (str): server url to the keycloak server or container
            realm_name (str): the keycloak realm to connect to (can be found in keycloak)
            client_id (str): the client id to use in keycloak realm (can be found in keycloak)
            client_secret (str): the client secret to use in keycloak realm (can be found in keycloak)  
        """
        self.store: Store = store
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

    def verify_token(self, token: str) -> AuthenticatedUser:
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
        return self._get_user_reponse(user_email)
        

    
    def _get_user_by_email(self, email: str):
        """
        Get user by email.
        args:
            email: str
        returns:
            User
        raises:
            ValueError: if the user is not found
        """
        user: User | None = self.store.get_user_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")
        return user
    
    def _check_role(self, user: User) -> str:
        """
        Check if user has the role.
        args:
            user: User
        returns:
            str
        raises:
            ValueError: if the user does not have access
        """
        if user.is_admin:
            return ADMIN
        if user.order_portal_login:
            return CUSTOMER
        raise ValueError('User does not have access')  

    def _get_user_reponse(self, email: str) -> AuthenticatedUser:
        """
        Get user response.
        args:
            email: str
        returns:
            AuthenticatedUser
        """
        user = self._get_user_by_email(email)
        role: str = self._check_role(user)
        return AuthenticatedUser(
            id=user.id,
            username=user.name,
            email=user.email,
            role=role,
        )
        
  