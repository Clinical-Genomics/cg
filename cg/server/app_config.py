from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    """
    Default values are overridden by environment variable at run-time.
    The environment variables are defined in the servers repo config/CGVS/config/container-env/cg.env
    """

    # Gunicorn settings
    gunicorn_workers: int = 4
    gunicorn_threads: int = 4
    gunicorn_bind: str = "0.0.0.0:8000"
    gunicorn_timeout: int = 400

    # Database settings
    cg_sql_database_uri: str = "sqlite:///"

    # Security settings
    cg_secret_key: str = "thisIsNotASafeKey"
    invoice_max_price: int = 750_000

    # LIMS settings
    lims_host: str = "lims_host"
    lims_username: str = "username"
    lims_password: str = "password"

    # Email settings
    support_system_email: str = "support@mail.com"
    email_uri: str = "smtp://localhost"

    # Trailblazer settings

    trailblazer_host: str = "trailblazer_host"
    trailblazer_service_account: str = "service_account"
    trailblazer_service_account_auth_file: str = "auth_file.json"

    # Freshdesk settings
    freshdesk_url: str = "https://company.freshdesk.com"
    freshdesk_api_key: str = "freshdesk_api_key"
    freshdesk_order_email_id: int = 10
    freshdesk_environment: str = "Stage"
    keycloak_client_url: str = "http://keycloak:8080"
    keycloak_realm_name: str = "orderportal"
    keycloak_client_id: str = "cg-flask-client"
    keycloak_client_secret_key: str = "cg-very-secret-password"
    keycloak_redirect_uri: str = "https://localhost:8000/auth/callback"


app_config = AppConfig()
