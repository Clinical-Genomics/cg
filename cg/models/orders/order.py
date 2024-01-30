from typing import Any

from pydantic.v1 import BaseModel, conlist, constr

from cg.models.orders.constants import OrderType
from cg.models.orders.samples import sample_class_for
from cg.store.models import Customer, Sample


class OrderIn(BaseModel):
    name: constr(min_length=2, max_length=Sample.order.property.columns[0].type.length)
    comment: str | None
    customer: constr(min_length=1, max_length=Customer.internal_id.property.columns[0].type.length)
    samples: conlist(Any, min_items=1)
    skip_reception_control: bool | None = None
    ticket: str | None
    order_type: OrderType | None = None

    @classmethod
    def parse_obj(cls, obj: dict, project: OrderType) -> "OrderIn":
        parsed_obj: OrderIn = super().parse_obj(obj)
        parsed_obj.parse_samples(project=project)
        parsed_obj.order_type = project
        return parsed_obj

    def parse_samples(self, project: OrderType) -> None:
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
            parsed_sample = sample_class_for(project=project).parse_obj(sample)
            parsed_sample.skip_reception_control = self.skip_reception_control
            parsed_samples.append(parsed_sample)
        self.samples = parsed_samples
