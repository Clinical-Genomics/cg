from pydantic import BaseModel, Field

from cg.models.orders.sample_base import NAME_PATTERN, StatusEnum


class ExistingSample(BaseModel):
    father: str | None = Field(None, pattern=NAME_PATTERN)
    internal_id: str
    mother: str | None = Field(None, pattern=NAME_PATTERN)
    status: StatusEnum | None = None

    @property
    def is_new(self) -> bool:
        return False
