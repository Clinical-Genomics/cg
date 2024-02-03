from pydantic import BaseModel


class UploadConfig(BaseModel):
    email: str
    log_dir: str
    account: str
