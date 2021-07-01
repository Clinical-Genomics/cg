from pathlib import Path
from typing import Optional

from pydantic import EmailStr

from cg.models.cg_config import EmailBaseSettings


class EmailInfo(EmailBaseSettings):
    receiver_email: EmailStr
    sender_email: EmailStr = "hiseq.clinical@hasta.scilifelab.se"
    subject: str
    message: str
    file: Optional[Path]
