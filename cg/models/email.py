from pydantic import EmailStr

from cg.models.cg_config import EmailBaseSettings


class EmailInfo(EmailBaseSettings):
    receiver_email: EmailStr
    subject: str
    message: str
