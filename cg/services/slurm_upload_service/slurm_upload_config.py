from pydantic import BaseModel

from cg.constants.priority import SlurmAccount


class SlurmUploadConfig(BaseModel):
    email: str
    log_dir: str
    account: SlurmAccount
