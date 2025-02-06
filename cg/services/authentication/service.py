from cg.store.models import User
from cg.store.store import Store
from keycloak import KeycloakOpenID
from cg.services.authentication.models import AuthenticatedUser


class AuthenticationService:
    """Authentication service"""

    def __init__(
        self, store: Store, server_url: str, client_id: str, client_secret: str, realm_name: str
    ):
        self.store: Store = store
        self.server_url: str = server_url
        self.client_id: str = client_id
        self.client_secret: str = client_secret
        self.realm_name: str = realm_name
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

    def get_user_by_email(self, email: str):
        """Get user by email."""
        user: User | None = self.store.get_user_by_email(email)
        if not user:
            raise ValueError(f"User with email {email} not found")

        return user
