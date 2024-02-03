from pydantic import BaseModel

from cg.constants.priority import SlurmAccount


class UploadConfig(BaseModel):
    email: str
    log_dir: str
    account: SlurmAccount
