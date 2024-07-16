from pydantic import BaseModel, Field
from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum


class Sample(BaseModel):
    application: str
    comment: str | None = None
    container: ContainerEnum
    container_name: str | None = None
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    require_qc_ok: bool
    volume: int | None = None
    well_position: int | None = None
