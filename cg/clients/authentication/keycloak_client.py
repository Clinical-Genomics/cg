from calendar import c
from keycloak import KeycloakOpenID
from keycloak import KeycloakConnectionError


class KeycloakClient:
    def __init__(self, server_url, client_id, realm_name, client_secret_key, redirect_uri):
        self.server_url = server_url
        self.client_id = client_id
        self.realm_name = realm_name
        self.client_secret_key = client_secret_key
        self.redirect_uri = redirect_uri
        self._client_instance: KeycloakOpenID | None = None

    def get_client(self) -> KeycloakOpenID:
        if self._client_instance is None:
            try:
                self._client_instance = KeycloakOpenID(
                    server_url=self.server_url,
                    client_id=self.client_id,
                    realm_name=self.realm_name,
                    client_secret_key=self.client_secret_key,
                )
            except KeycloakConnectionError as error:
                raise KeycloakConnectionError(f"Failed to connect to Keycloak: {error}")
            except Exception as error:
                raise Exception(f"An error occurred while creating Keycloak client: {error}")
        return self._client_instance

    def get_auth_url(self, scope: str = "openid profile email") -> str:
        """Get the authorization URL for user login."""
        client = self.get_client()
        return client.auth_url(redirect_uri=self.redirect_uri, scope=scope)

    def logout_user(self, refresh_token: str) -> None:
        """
        Logout a user.
        Args:
            refresh_token: the refresh token stored in the session
        """
        client: KeycloakOpenID = self.get_client()
        client.logout(refresh_token)

    def get_token(self, code: str) -> dict:
        """
        Get a token using the authorisation code.
        Args:
            code: code retrieved request
        """
        client: KeycloakOpenID = self.get_client()
        return client.token(
            grant_type="authorization_code", code=code, redirect_uri=self.redirect_uri
        )

    def get_user_info(self, access_token: str) -> dict:
        """Get the user info for a provided access token.

        Args:
            access_token: access token given by keycloak

        Returns:
            dict: with the user information
        """
        client: KeycloakOpenID = self.get_client()
        return client.userinfo(access_token)