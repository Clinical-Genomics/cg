from pydantic import BaseModel, Field, ValidationError, model_validator
from pydantic_core import InitErrorDetails

from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum


class OrderSample(BaseModel):
    application: str
    comment: str | None = None
    container: ContainerEnum
    container_name: str | None = None
    internal_id: str | None = None
    name: str = Field(pattern=NAME_PATTERN, min_length=2, max_length=128)
    require_qc_ok: bool = False
    volume: int | None = None
    well_position: str | None = None

    @model_validator(mode="after")
    def validate_container_name(self):
        if self.container == ContainerEnum.plate and not self.container_name:
            error_details = InitErrorDetails(
                type="missing", loc=("container_name",), input=self.container_name, ctx={}
            )
            raise ValidationError.from_exception_data(
                title=self.__class__.__name__, line_errors=[error_details]
            )

    @model_validator(mode="after")
    def validate_well_position(self):
        if self.container == ContainerEnum.plate and not self.well_position:
            error_details = InitErrorDetails(
                type="missing", loc=("well_position",), input=self.well_position, ctx={}
            )
            raise ValidationError.from_exception_data(
                title=self.__class__.__name__, line_errors=[error_details]
            )
