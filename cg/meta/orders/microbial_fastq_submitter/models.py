from pydantic import BaseModel

from cg.store.models import Customer, Sample


class MicrobialFastqDTO(BaseModel):
    customer: Customer
    order: str
    samples: list[Sample]
