from pydantic import BaseModel, Field, PrivateAttr, model_validator

from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum, PriorityEnum


class Sample(BaseModel):
    application: str = Field(min_length=1)
    _case_name: str = PrivateAttr(default="")
    _case_priority: PriorityEnum | None = PrivateAttr(default=None)
    comment: str | None = None
    container: ContainerEnum
    container_name: str | None = Field(default=None, pattern=NAME_PATTERN)
    _generated_lims_id: str | None = PrivateAttr(default=None)  # Will be populated by LIMS
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    volume: int | None = None
    well_position: str | None = None

    @property
    def is_new(self) -> bool:
        return True

    @property
    def is_on_plate(self) -> bool:
        return self.container == ContainerEnum.plate

    @model_validator(mode="before")
    @classmethod
    def convert_empty_strings_to_none(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if value == "":
                    data[key] = None
        return data

    @model_validator(mode="after")
    def set_tube_name_default(self):
        if self.container == ContainerEnum.tube and not self.container_name:
            self.container_name = self.name
        return self
