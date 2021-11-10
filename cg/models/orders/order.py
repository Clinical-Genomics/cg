from typing import Optional, Any

from cgmodels.cg.constants import Pipeline
from pydantic import BaseModel, constr, conlist

from cg.models.orders.constants import OrderType
from cg.models.orders.samples import (
    OrderInSample,
    MipDnaSample,
    BalsamicSample,
    FastqSample,
    MetagenomeSample,
    MicrobialSample,
    MipRnaSample,
    RmlSample,
    SarsCov2Sample,
)
from cg.store import models
from cg.utils.StrEnum import StrEnum


class OrderIn(BaseModel):
    name: constr(min_length=2, max_length=models.Sample.order.property.columns[0].type.length)
    comment: Optional[str]
    customer: constr(
        min_length=1, max_length=models.Customer.internal_id.property.columns[0].type.length
    )
    samples: conlist(OrderInSample, min_items=1)
    ticket: Optional[str]

    @classmethod
    def parse_obj(cls, obj: dict, project: OrderType):
        parsed_obj = super().parse_obj(obj)
        parsed_obj.parse_samples(project=project)
        return parsed_obj

    def parse_samples(self, project: OrderType):
        """
        Parses samples of by the type given by the project

        Parameters:
            project (OrderType): type of project

        Returns:
            Nothing
        """
        parsed_samples = []

        sample: dict
        for sample in self.samples:
            parsed_sample = self.BaseSample(project=project).parse_obj(sample)

            if parsed_sample:
                parsed_samples.append(parsed_sample)

        self.samples = parsed_samples
