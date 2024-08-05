from pydantic_settings import BaseSettings


class AppConfig(BaseSettings):
    gunicorn_workers: int = 4
    gunicorn_threads: int = 4
    gunicorn_bind: str
    gunicorn_timeout: int = 400
    cg_sql_database_uri: str
    cg_secret_key: str = "thisIsNotASafeKey"
    invoice_max_price: int = 750_000
    lims_host: str
    lims_username: str
    lims_password: str
    osticket_api_key: str
    osticket_domain: str
    support_system_email: str
    email_uri: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    trailblazer_host: str
    trailblazer_service_account: str
    trailblazer_service_account_auth_file: str


app_config = AppConfig()
