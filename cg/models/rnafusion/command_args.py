from pathlib import Path
from typing import Optional, Union

from pydantic import BaseModel


class CommandArgs(BaseModel):
    """Model for arguments and options supported."""

    log: Optional[Union[str, Path]] = None
    resume: Optional[bool] = None
    profile: Optional[str] = None
    stub: Optional[bool] = None
    config: Optional[Union[str, Path]] = None
    name: Optional[str] = None
    revision: Optional[str] = None
    wait: Optional[str] = None
    id: Optional[str] = None
    with_tower: Optional[bool] = None
    use_nextflow: Optional[bool] = None
    compute_env: Optional[str] = None
    work_dir: Optional[Union[str, Path]] = None
    params_file: Optional[Union[str, Path]] = None
