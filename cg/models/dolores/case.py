from typing import Optional, Union, List

from cgmodels.cg.constants import Pipeline
from pydantic import BaseModel, validator

from cg.constants import DataDelivery
from cg.constants.constants import CaseAction
from cg.constants.priority import Priority, PriorityChoices


class Case(BaseModel):
    action: CaseAction
    case_id: str
    comment: Optional[str]
    customer_id: str
    customer_case_id: str
    data_analysis: Pipeline
    data_delivery: DataDelivery
    gene_panels: Optional[List[str]]
    order_id: int
    priority: Union[Priority, PriorityChoices]

    @validator("priority", always=True)
    def convert_priority(cls, value: Union[Priority, PriorityChoices]) -> Priority:
        if isinstance(value, str):
            return Priority[value]
        return value
