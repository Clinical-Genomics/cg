from pydantic import BaseModel

from cg.models.orders.sample_base import ContainerEnum
from cg.services.validation_service.constants import TissueBlockEnum


class OrderSample(BaseModel):
    application: str
    comment: str
    container: ContainerEnum
    container_name: str | None = None
    formalin_fixation_time: int | None = None
    name: str
    post_formalin_fixation_time: int | None = None
    source: str
    tissue_block_size: TissueBlockEnum | None = None
    volume: int | None = None
    well_position: str | None = None
