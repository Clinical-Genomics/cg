from pydantic import BaseModel, Field, model_validator

from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum


class Sample(BaseModel):
    application: str = Field(min_length=1)
    comment: str | None = None
    container: ContainerEnum
    container_name: str | None = None
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
