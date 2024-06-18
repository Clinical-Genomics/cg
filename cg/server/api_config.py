from pydantic_settings import BaseSettings


class APIConfig(BaseSettings):
    gunicorn_workers: int
    gunicorn_threads: int
    gunicorn_bind: str
    gunicorn_timeout: int
    cg_sql_database_uri: str
    cg_secret_key: str
    lims_host: str
    lims_username: str
    lims_password: str
    osticket_api_key: str
    osticket_domain: str
    support_system_email: str
    email_uri: str
    google_oauth_client_id: str
    google_oauth_client_secret: str
    cg_enable_admin: bool
    trailblazer_host: str
    trailblazer_service_account: str
    trailblazer_service_account_auth_file: str


def get_api_config():
    return APIConfig()
