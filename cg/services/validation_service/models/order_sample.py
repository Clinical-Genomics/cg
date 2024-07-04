from pydantic import BaseModel, Field, model_validator

from cg.models.orders.sample_base import NAME_PATTERN, ContainerEnum
from cg.services.validation_service.models.sample_validators import (
    validate_required_container_name,
    validate_required_volume,
    validate_required_well_position,
)


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

    _validate_required_container_name = model_validator(mode="after")(
        validate_required_container_name
    )
    _validate_required_volume = model_validator(mode="after")(validate_required_volume)
    _validate_required_well_position = model_validator(mode="after")(
        validate_required_well_position
    )
