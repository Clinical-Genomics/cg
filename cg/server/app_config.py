from pydantic_settings import BaseSettings
import os


class AppConfig(BaseSettings):
    """Default values are overridden by environment variable at run-time."""

    gunicorn_workers: int = int(os.getenv("GUNICORN_WORKERS", 4))
    gunicorn_threads: int = int(os.getenv("GUNICORN_THREADS", 4))
    gunicorn_bind: str = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
    gunicorn_timeout: int = int(os.getenv("GUNICORN_TIMEOUT", 400))
    cg_sql_database_uri: str = os.getenv("CG_SQL_DATABASE_URI", "sqlite:///")
    secret_key: str = os.getenv("CG_SECRET_KEY", "thisIsNotASafeKey")
    invoice_max_price: int = int(os.getenv("INVOICE_MAX_PRICE", 750_000))
    lims_host: str = os.getenv("LIMS_HOST", "lims_host")
    lims_username: str = os.getenv("LIMS_USERNAME", "username")
    lims_password: str = os.getenv("LIMS_PASSWORD", "password")
    support_system_email: str = os.getenv("SUPPORT_SYSTEM_EMAIL", "support@mail.com")
    email_uri: str = os.getenv("EMAIL_URI", "smtp://localhost")
    google_oauth_client_id: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "client_id")
    google_oauth_client_secret: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "client_secret")
    trailblazer_host: str = os.getenv("TRAILBLAZER_HOST", "trailblazer_host")
    trailblazer_service_account: str = os.getenv("TRAILBLAZER_SERVICE_ACCOUNT", "service_account")
    trailblazer_service_account_auth_file: str = os.getenv(
        "TRAILBLAZER_SERVICE_ACCOUNT_AUTH_FILE", "auth_file.json"
    )
    freshdesk_url: str = os.getenv("FRESHDESK_URL", "https://company.freshdesk.com")
    freshdesk_api_key: str = os.getenv("FRESHDESK_API_KEY", "freshdesk_api_key")
    freshdesk_order_email_id: int = int(os.getenv("FRESHDESK_ORDER_EMAIL_ID", 10))
    freshdesk_environment: str = os.getenv("FRESHDESK_ENVIRONMENT", "Stage")


app_config = AppConfig()
