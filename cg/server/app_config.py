from cycler import K
from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """Default values are overridden by environment variable at run-time."""

    gunicorn_workers: int = 4
    gunicorn_threads: int = 4
    gunicorn_bind: str = "0.0.0.0:8000"
    gunicorn_timeout: int = 400
    cg_sql_database_uri: str = "sqlite:///"
    cg_secret_key: str = "thisIsNotASafeKey"
    invoice_max_price: int = 750_000
    lims_host: str = "lims_host"
    lims_username: str = "username"
    lims_password: str = "password"
    support_system_email: str = "support@mail.com"
    email_uri: str = "smtp://localhost"
    trailblazer_host: str = "trailblazer_host"
    trailblazer_service_account: str = "service_account"
    trailblazer_service_account_auth_file: str = "auth_file.json"
    freshdesk_url: str = "https://company.freshdesk.com"
    freshdesk_api_key: str = "freshdesk_api_key"
    freshdesk_order_email_id: int = 10
    freshdesk_environment: str = "Stage"
    keycloak_client_url: str = "server_url"
    keycloak_realm_name = "realm"
    keycloak_client_id = "client"
    keycloak_client_secret_key = "client_secret"
    keycloak_redirect_uri = "redirect_uri"

app_config = AppConfig()
