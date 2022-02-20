from datetime import datetime
from typing import List, Optional, Union

from pydantic import BaseModel, validator
from cg.constants import Pipeline
from cg.models.report.sample import SampleModel
from cg.models.report.validators import (
    validate_empty_field,
    validate_supported_pipeline,
    validate_list,
)


class CustomerModel(BaseModel):
    """
    Customer model associated to the delivery report generated

    Attributes:
        name: customer name; source: statusDB/family/customer/name
        id: customer internal ID; source: statusDB/family/customer/internal_id
        invoice_address: customers invoice address; source: statusDB/family/customer/invoice_address
        scout_access: whether the customer has access to scout or not; source: statusDB/family/customer/scout_access
    """

    name: str
    id: Optional[str]
    invoice_address: Optional[str]
    scout_access: bool

    _values = validator("name", "id", "invoice_address", always=True, allow_reuse=True)(
        validate_empty_field
    )


class CaseModel(BaseModel):
    """
    Defines the case/family model

    Attributes:
        name: case name; source: StatusDB/family/name
        pipeline: data analysis requested by the customer; source: StatusDB/family/data_analysis
        panels: list of case specific panels; MIP specific; source: StatusDB/family/panels
        samples: list of samples associated to a case/family
    """

    name: str
    pipeline: Pipeline
    panels: Union[List[str], str] = None
    samples: List[SampleModel]

    _name = validator("name", always=True, allow_reuse=True)(validate_empty_field)
    _pipeline = validator("pipeline", always=True, allow_reuse=True)(validate_supported_pipeline)
    _panels = validator("panels", always=True, allow_reuse=True)(validate_list)


class ReportModel(BaseModel):
    """
    Model that defines the report attributes to render

    Attributes:
        customer: customer attributes
        version: delivery report version; source: StatusDB/analysis/family/analyses(/index)
        date: report generation date; source: CG runtime
        case: case attributes
        accredited: whether the report is accredited or not; source: all(StatusDB/application/accredited)
    """

    customer: CustomerModel
    version: Union[int, str] = None
    date: Union[datetime, str]
    case: CaseModel
    accredited: bool

    _version = validator("version", always=True, allow_reuse=True)(validate_empty_field)
