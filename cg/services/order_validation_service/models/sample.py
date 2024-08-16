from pydantic import BaseModel, ConfigDict, Field

from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum


class Sample(BaseModel):
    application: str | None = None
    comment: str | None = None
    container: ContainerEnum | None = None
    container_name: str | None = None
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    require_qc_ok: bool | None = None
    volume: int | None = None
    well_position: str | None = None

    model_config = ConfigDict(str_min_length=1)

    @property
    def is_new(self) -> bool:
        return not self.internal_id
