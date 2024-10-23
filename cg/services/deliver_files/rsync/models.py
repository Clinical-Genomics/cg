from pydantic import BaseModel


class RsyncDeliveryConfig(BaseModel):
    account: str
    base_path: str
    covid_destination_path: str
    covid_report_path: str
    destination_path: str
    mail_user: str
