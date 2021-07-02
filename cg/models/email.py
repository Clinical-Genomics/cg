from pathlib import Path
from typing import Optional

from pydantic import EmailStr

from cg.models.cg_config import EmailBaseSettings


class EmailInfo(EmailBaseSettings):
    receiver_email: str
    sender_email: str = "hiseq.clinical@hasta.scilifelab.se"
    subject: str
    message: str
    file: Optional[Path]
