from keycloak import KeycloakOpenID
from keycloak import KeycloakConnectionError


class KeycloakClient:
    def __init__(self, server_url, client_id, realm_name, client_secret_key):
        self.server_url = server_url
        self.client_id = client_id
        self.realm_name = realm_name
        self.client_secret_key = client_secret_key
        
        
    def get_client(self) -> KeycloakOpenID:
        try:
            return KeycloakOpenID(
                server_url=self.server_url,
                client_id=self.client_id,
                realm_name=self.realm_name,
                client_secret_key=self.client_secret_key,
            )
        except KeycloakConnectionError as error:
            raise KeycloakConnectionError(f"Failed to connect to Keycloak: {error}")
        except Exception as error:
            raise Exception(f"An error occurred while creating Keycloak client: {error}")
