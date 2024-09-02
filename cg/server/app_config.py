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
    google_oauth_client_id: str = "client_id"
    google_oauth_client_secret: str = "client_secret"
    trailblazer_host: str = "trailblazer_host"
    trailblazer_service_account: str = "service_account"
    trailblazer_service_account_auth_file: str = "auth_file.json"
    freshdesk_url: str = "https://company.freshdesk.com"
    freshdesk_api_key: str = "freshdesk_api_key"
    freshdesk_order_email_id: int = 10
    freshdesk_environment: str = "Stage"


app_config = AppConfig()
