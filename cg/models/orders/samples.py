from pydantic.v1 import BaseModel, constr, validator

from cg.constants import DataDelivery
from cg.constants.constants import GenomeVersion, Workflow
from cg.models.orders.constants import OrderType
from cg.models.orders.sample_base import (
    NAME_PATTERN,
    ContainerEnum,
    ControlEnum,
    PriorityEnum,
    SexEnum,
    StatusEnum,
)
from cg.store.models import Application, Case, Panel, Sample


class OrderInSample(BaseModel):
    # Order portal specific
    internal_id: constr(max_length=Sample.internal_id.property.columns[0].type.length) | None
    _suitable_project: OrderType = None
    application: constr(max_length=Application.tag.property.columns[0].type.length)
    comment: constr(max_length=Sample.comment.property.columns[0].type.length) | None
    skip_reception_control: bool | None = None
    data_analysis: Workflow
    data_delivery: DataDelivery
    name: constr(
        regex=NAME_PATTERN,
        min_length=2,
        max_length=Sample.name.property.columns[0].type.length,
    )
    priority: PriorityEnum = PriorityEnum.standard
    require_qc_ok: bool = False
    volume: str
    concentration_ng_ul: str | None

    @classmethod
    def is_sample_for(cls, project: OrderType):
        return project == cls._suitable_project


def sample_class_for(project: OrderType):
    """Get the sample class for the specified project

    Args:
        project     (OrderType):    Project to get sample subclass for
    Returns:
        Subclass of OrderInSample
    """

    def all_subclasses(cls):
        """Get all subclasses recursively for a class

        Args:
            cls     (Class):    Class to get all subclasses for
        Returns:
            Set of Subclasses of cls
        """
        if cls.__subclasses__():
            return set(cls.__subclasses__()).union(
                [s for c in cls.__subclasses__() for s in all_subclasses(c)]
            )

        return []

    for sub_cls in all_subclasses(OrderInSample):
        if sub_cls.is_sample_for(project):
            return sub_cls

    raise ValueError
